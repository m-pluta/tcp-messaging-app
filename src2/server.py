# Standard Library Imports
import os
import sys
import socket
import threading
import select

# Local Imports
from packet_type import PacketType
from packet import (
    HEADER_SIZE,
    encode_header,
    decode_header
)
from log_event import LogEvent
from logger import Logger


class ClientConnection:
    def __init__(self, socket: socket.socket):
        self.username = None
        self.socket = socket


class Server:
    def __init__(self, port: int):
        # Init key variables and create logger
        self.port = port
        self.logger = Logger('./server.log')
        self.files_path = 'download'
        self.connections: list[ClientConnection] = []

    def start(self):
        # Start a new thread to handle communication with the server
        server_thread = threading.Thread(target=self.run_server)
        server_thread.daemon = True
        server_thread.start()

        self.handle_cli_input()

    def handle_cli_input(self):
        while True:
            try:
                input()
            except KeyboardInterrupt:
                print('Detected Keyboard Interrupt')
                sys.exit(0) 

    def run_server(self):
        # Begin starting the server
        self.logger.log(LogEvent.SERVER_INIT_START, port=self.port)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("", self.port))
        self.socket.listen(1)

        self.logger.log(LogEvent.SERVER_STARTED, port=self.port)

        self.listen()

    def listen(self):
        self.logger.log(LogEvent.SERVER_LISTENING, port=self.port)

        while True:
            readables = [self.socket] + [c.socket for c in self.connections]
            readable, _, _ = select.select(readables, [], [])

            for sock in readable:
                if sock is self.socket:
                    client_socket, addr = self.socket.accept()
                    self.logger.log(LogEvent.USER_CONNECT, ip_address=addr[0], client_port=addr[1])

                    self.connections.append(ClientConnection(client_socket))
                else:
                    self.process_socket(sock)

    def process_socket(self, socket: socket.socket):
        data = socket.recv(HEADER_SIZE)
        conn = self.get_conn_by_socket(socket)
        if not data:
            self.close_conn(conn)
            return
        
        expected_type, expected_size, params = decode_header(data)
        message = socket.recv(expected_size).decode()

        if expected_type == PacketType.USERNAME:
            username = params.get('username')
            self.process_metadata_packet(conn, username)

        elif expected_type == PacketType.OUT_MESSAGE:
            recipient = params.get('recipient')
            self.process_message_packet(conn, recipient, message)

        elif expected_type == PacketType.FILE_LIST_REQUEST:
            self.process_file_list_request(conn)

        elif expected_type == PacketType.DOWNLOAD_REQUEST:
            filename = params.get('filename')
            self.process_download_request(conn, filename)

    def process_metadata_packet(self, conn: ClientConnection, username: str):
        if username in self.get_connected_users():
            self.handle_duplicate_username(conn)
            return
        conn.username = username

        self.logger.log(LogEvent.PACKET_RECEIVED, username=username, content=username)

        message = f'{username} has joined the chat.'.encode()
        header = encode_header(PacketType.ANNOUNCEMENT, len(message))
        self.broadcast(header + message, exclude=[username])

    def handle_duplicate_username(self, conn: ClientConnection):
        connected_users_list = ", ".join(self.get_connected_users())
        
        message = connected_users_list.encode()
        header = encode_header(PacketType.DUPLICATE_USERNAME, len(message))
        conn.socket.sendall(header + message)

    def process_message_packet(self, conn: ClientConnection, recipient: [None|str], message: str):
        self.logger.log(LogEvent.PACKET_RECEIVED, username=conn.username, content=message)

        message = message.encode()
        header = encode_header(PacketType.IN_MESSAGE, len(message), sender=conn.username)

        if recipient:
            self.unicast(header + message, recipient)
        else:
            self.broadcast(header + message, exclude=[conn.username])

    def process_file_list_request(self, conn: ClientConnection):
        self.logger.log(LogEvent.FILE_LIST_REQUEST, username=conn.username)

        try:
            with os.scandir(self.files_path) as entries:
                files = [f'|-- {e.name}\n' for e in entries if e.is_file()]
        except FileNotFoundError:
            files = []

        if files:
            message = f'download\n{"".join(files)}'.encode()
            header = encode_header(PacketType.FILE_LIST, len(message))
            conn.socket.sendall(header + message)
        else:
            print(f'No files found in {self.files_path}')
            # TODO: handle no files on server
        pass

    def process_download_request(self, conn: ClientConnection, filename: str):
        filepath = f'{self.files_path}/{filename}'
        try:
            with open(filepath, 'rb') as f:
                file = f.read()
        except FileNotFoundError:
            print(f"File not found: {filepath}")
            return
        
        header = encode_header(PacketType.DOWNLOAD, len(file), filename=filename)
        conn.socket.sendall(header + file)
        self.logger.log(LogEvent.DOWNLOAD_REQUEST, username=conn.username, filename=filename)

    def broadcast(self, data: bytes, exclude: list[str]=[]):
        for conn in self.connections:
            if conn.username in exclude:
                continue
            conn.socket.sendall(data)
            self.logger.log(LogEvent.PACKET_SENT, username=conn.username, content=data[HEADER_SIZE:].decode())

    def unicast(self, data: bytes, recipient: str):
        for conn in self.connections:
            if conn.username == recipient:
                conn.socket.sendall(data)
                self.logger.log(LogEvent.PACKET_SENT, username=recipient, content=data[HEADER_SIZE:].decode())

    def get_conn_by_socket(self, socket: socket.socket):
        for conn in self.connections:
            if conn.socket == socket:
                return conn
        return None
    
    def get_connected_users(self):
        return [conn.username for conn in self.connections if conn.username]

    def close_conn(self, conn: ClientConnection):
        if conn.socket.fileno() != -1:
            conn.socket.shutdown(socket.SHUT_RDWR)
            conn.socket.close()

        message = f'{conn.username} disconnected'.encode()
        header = encode_header(PacketType.ANNOUNCEMENT, len(message))
        self.broadcast(header + message, exclude=[conn.username])

        self.connections.remove(conn)


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
