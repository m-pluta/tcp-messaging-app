# Standard Library Imports
import sys
import socket
import threading
import os

# Local Imports
from logger import (
    Logger,
    LogEvent,
)
from packet import (
    ENCODING,
    HEADER_SIZE,
    PACKET_SIZE,
    DownloadPacket,
    HeaderPacket,
    PacketType,
    Packet,
    InMessagePacket,
    AnnouncementPacket,
    DuplicateUsernamePacket
)
from utility import extract_delimiter, recv_to_buffer


class ClientConnection:
    def __init__(self, socket: socket.socket, address: tuple):
        self.socket = socket
        self.ip_address = address[0]
        self.port = address[1]
        self.username = None

    def send(self, bytes: bytearray):
        self.socket.sendall(bytes)


class Server:
    def __init__(self, port):
        # Init key variables and create logger
        self.port = port
        self.logger = Logger('./server.log')
        self.files_path = 'download'
        self.connections = {}

    def start(self):
        # Begin starting the server
        self.logger.log(LogEvent.SERVER_INIT_START, port=self.port)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.socket.bind(("", self.port))
        self.socket.listen(1)
        self.is_running = True

        self.logger.log(LogEvent.SERVER_STARTED, port=self.port)

        self.listen()

    def listen(self):
        self.logger.log(LogEvent.SERVER_LISTENING, port=self.port)

        while self.is_running:
            try:
                # New client tries to establish a connection
                client_socket, addr = self.socket.accept()
                conn = ClientConnection(client_socket, addr)
                self.logger.log(LogEvent.USER_CONNECT,
                                ip_address=conn.ip_address,
                                client_port=conn.port)

                # Start a new thread to handle communication with new client
                client_thread = threading.Thread(target=self.handle_client,
                                                 args=(conn,))
                client_thread.start()
                self.logger.log(LogEvent.USER_THREAD_STARTED,
                                ip_address=conn.ip_address,
                                client_port=conn.port)
            except KeyboardInterrupt:
                break

        self.close()

    def handle_client(self, conn: ClientConnection):
        while True:
            # Check if client disconnected
            header_data = conn.socket.recv(HEADER_SIZE)
            if not header_data:
                break

            header: dict = HeaderPacket.decode(header_data)

            content_data = recv_to_buffer(conn.socket,
                                          header.get('size'))

            match header.get('type'):
                case PacketType.METADATA:
                    self.process_metadata_packet(content_data, conn)
                case PacketType.OUT_MESSAGE:
                    self.process_message_packet(content_data, conn)
                case PacketType.FILE_LIST_REQUEST:
                    self.process_file_list_request_packet(conn)
                case PacketType.DOWNLOAD_REQUEST:
                    self.process_download_request_packet(content_data, conn)

        self.close_client(conn)

    def process_metadata_packet(self, data, client_conn):
        username = data.decode(ENCODING)
        if username in self.connections:
            self.handle_duplicate_username(client_conn)
            return

        self.connections[username] = client_conn
        client_conn.username = username

        self.logger.log(LogEvent.PACKET_RECEIVED,
                        username=client_conn.username,
                        content=client_conn.username)

        # Send announcement to all other clients
        packet = AnnouncementPacket(
            content=f'{client_conn.username} has joined the chat.')
        bytes = packet.to_bytes()

        self.broadcast(bytes, exclude=[client_conn.username])

    def handle_duplicate_username(self, client_conn):
        current_users = ", ".join(self.connections.keys())
        packet = DuplicateUsernamePacket(content=current_users)
        bytes = packet.to_bytes()
        client_conn.socket.sendall(bytes)

    def process_message_packet(self, data, client_conn):
        recipient = extract_delimiter(data[:PACKET_SIZE].decode(ENCODING))
        message_content = data[PACKET_SIZE:].decode(ENCODING)

        self.logger.log(LogEvent.PACKET_RECEIVED,
                        username=client_conn.username,
                        content=message_content)

        packet = InMessagePacket(content=message_content,
                                 sender=client_conn.username)

        bytes = packet.to_bytes()

        if recipient:
            self.unicast(bytes, recipient)
        else:
            self.broadcast(bytes, exclude=[client_conn.username])

    def process_file_list_request_packet(self, client_conn):
        self.logger.log(LogEvent.FILE_LIST_REQUEST,
                        username=client_conn.username)
        try:
            with os.scandir(self.files_path) as entries:
                files = [e.name for e in entries if e.is_file()]
        except FileNotFoundError:
            files = []

        if files:
            file_list = " ".join(files)

            packet = InMessagePacket(sender=None, content=file_list)
            bytes = packet.to_bytes()
            self.unicast(bytes, client_conn.username)
        else:
            print(f'No files found in {self.files_path}')
            # TODO: handle no files on server

    def process_download_request_packet(self, data, client_conn):
        filename = data.decode(ENCODING)
        filepath = f'{self.files_path}/{filename}'

        try:
            with open(filepath, 'rb') as file:
                file_bytes = file.read()
        except FileNotFoundError:
            print(f"File not found: {filepath}")
            return None
        
        print(f'Raw file bytes: {len(file_bytes)}')
        packet = DownloadPacket(filename, file_bytes)
        bytes = packet.to_bytes()
        print(f'Total file bytes: {len(bytes)}')
        print(f'Header bytes: {bytes[:HEADER_SIZE]}')
        client_conn.socket.sendall(bytes)

        self.logger.log(LogEvent.DOWNLOAD_REQUEST,
                        username=client_conn.username,
                        filename=filename)

    def unicast(self, bytes, recipient):
        if recipient in self.connections:

            recipient_socket = self.connections[recipient].socket
            recipient_socket.sendall(bytes)

            # self.logger.log(LogEvent.PACKET_SENT, username=recipient,
            #                 content=bytes.decode())

    def broadcast(self, bytes, exclude=[]):
        for recipient, recipient_conn in self.connections.items():
            if recipient in exclude:
                continue

            recipient_conn.socket.sendall(bytes)

            # self.logger.log(LogEvent.PACKET_SENT, username=recipient,
            #                 content=packet.content)

    def close_client(self, client_conn):
        client_username = client_conn.username

        if client_username in self.connections:
            # TODO: Send closed socket a message saying it is being closed.

            client_conn.socket.close()
            del self.connections[client_username]
            self.logger.log(LogEvent.USER_DISCONNECT, username=client_username)

            # Send announcement to all other clients
            packet = AnnouncementPacket(
                (f'{client_username} has left the chat.')
            )
            bytes = packet.to_bytes()
            self.broadcast(bytes, exclude=[client_username])

    def close_client_sockets(self):
        clients = list(self.connections.keys())
        for client in clients:
            self.close_client(self.connections[client])

        # Handle someone connecting while the client sockets were being closed
        if self.connections:
            self.close_client_sockets()

    def close(self):
        self.close_client_sockets()
        self.is_running = False
        self.socket.close()
        self.logger.log(LogEvent.SERVER_CLOSE)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python server.py [port]")
        sys.exit(1)

    # Convert port input parameter to integer
    try:
        port = int(sys.argv[1])
    except ValueError:
        print("Invalid port number. Port must be an integer.")
        sys.exit(1)

    # Create and start server
    server = Server(port)
    server.start()
