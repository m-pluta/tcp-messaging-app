# Standard Library Imports
import sys
import socket
import threading
import os
import time

# Local Imports
from logger import (
    Logger,
    LogEvent,
)
from packet import (
    HEADER_SIZE,
    PacketType,
    Packet,
    InMessagePacket,
    AnnouncementPacket,
    send_packet
)


class ClientConnection:
    def __init__(self, socket, address):
        self.socket = socket
        self.ip_address = address[0]
        self.port = address[1]
        self.username = None


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

        try:
            self.socket.bind(("", self.port))
        except Exception:
            self.logger.log(LogEvent.SERVER_BIND_ERROR)
            return

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

    def handle_client(self, conn):
        expected_size = HEADER_SIZE
        while True:
            # Check if client disconnected
            data = conn.socket.recv(expected_size)
            if not data:
                break

            # Handle client sending a packet to the server
            packet = Packet.loads(data.decode())

            match PacketType(packet.get('type')):
                case PacketType.HEADER:
                    expected_size = packet.get('size')
                    continue
                case PacketType.METADATA:
                    self.process_metadata_packet(packet, conn)
                case PacketType.OUT_MESSAGE:
                    self.process_message_packet(packet, conn)
                case PacketType.FILE_LIST_REQUEST:
                    self.process_file_list_request_packet(conn)
                case PacketType.DOWNLOAD_REQUEST:
                    self.process_download_request_packet(packet, conn)

            expected_size = HEADER_SIZE

        self.close_client(conn)

    def process_metadata_packet(self, incoming_packet, client_conn):
        # Extract username from metadata
        username = incoming_packet.get('username')

        self.connections[username] = client_conn
        client_conn.username = username

        self.logger.log(LogEvent.PACKET_RECEIVED,
                        username=client_conn.username,
                        content=client_conn.username)

        # Send announcement to all other clients
        packet = AnnouncementPacket(
            f'{client_conn.username} has joined the chat.')
        self.broadcast(packet, exclude=[client_conn.username])

    def process_message_packet(self, incoming_packet, client_conn):
        packet_content = incoming_packet.get('content')
        self.logger.log(LogEvent.PACKET_RECEIVED,
                        username=client_conn.username,
                        content=packet_content)

        recipient = incoming_packet.get('recipient')

        packet = InMessagePacket(content=packet_content,
                                 sender=client_conn.username)

        if recipient:
            self.unicast(packet, recipient)
        else:
            self.broadcast(packet, exclude=[client_conn.username])

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
            self.unicast(packet, client_conn.username)
        else:
            print(f'No files found in {self.files_path}')
            # TODO: handle no files on server

    def process_download_request_packet(self, incoming_packet, client_conn):
        filename = incoming_packet.get('filename')
        self.logger.log(LogEvent.DOWNLOAD_REQUEST,
                        username=client_conn.username,
                        filename=filename)

    def unicast(self, packet: Packet, recipient):
        if recipient in self.connections:

            recipient_socket = self.connections[recipient].socket
            send_packet(recipient_socket, packet)

            self.logger.log(LogEvent.PACKET_SENT, username=recipient,
                            content=packet.content)

    def broadcast(self, packet: Packet, exclude=[]):
        for recipient, recipient_conn in self.connections.items():
            if recipient in exclude:
                continue

            send_packet(recipient_conn.socket, packet)

            self.logger.log(LogEvent.PACKET_SENT, username=recipient,
                            content=packet.content)

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
            self.broadcast(packet, exclude=[client_username])


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
