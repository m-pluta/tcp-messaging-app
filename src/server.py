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
import logging


class ClientConnection:
    def __init__(self, socket: socket.socket, addr: tuple[str, int]):
        self.username = None
        self.socket = socket
        self.addr = addr


class Server:
    def __init__(self, port: int):
        # Init key variables and logger
        self.port = port
        self.files_path = 'download'
        os.makedirs(self.files_path, exist_ok=True)
        self.connections: list[ClientConnection] = []

        format = '%(asctime)s | %(levelname)-8s | %(message)s'
        logging.basicConfig(level=logging.INFO,
                            filename='server.log',
                            filemode='a',
                            format=format)

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
                logging.critical('Detected Keyboard Interrupt')
                self.close()

    def run_server(self):
        # Begin starting the server
        logging.info(f'Server starting on port {self.port}')

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("", self.port))
            self.socket.listen(1)
        except Exception:
            logging.critical(f'Error starting server on port {self.port}')

        logging.info(f'Server started on port {self.port}')
        self.listen()

    def listen(self):
        logging.info(f'Server listening on port {self.port}')

        while True:
            readables = [self.socket] + [c.socket for c in self.connections]
            readable, _, _ = select.select(readables, [], [])

            for sock in readable:
                if sock is self.socket:
                    client_socket, addr = self.socket.accept()
                    print(f'New client connection {addr[0]}:{addr[1]}')
                    logging.info(f'New client connection {addr[0]}:{addr[1]}')

                    new_conn = ClientConnection(client_socket, addr)
                    self.connections.append(new_conn)
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
            logging.warning(f'{conn.addr[0]}:{conn.addr[1]} attempted to join'
                            f' using a duplicate username: "{username}"')
            self.handle_duplicate_username(conn)
            return
        conn.username = username

        logging.info(f'{conn.addr[0]}:{conn.addr[1]} identified as {username}')

        message = f'{username} has joined the chat'.encode()
        header = encode_header(PacketType.ANNOUNCEMENT, len(message))
        self.broadcast(header + message, exclude=[username])

    def handle_duplicate_username(self, conn: ClientConnection):
        connected_users_list = ", ".join(self.get_connected_users())

        message = connected_users_list.encode()
        header = encode_header(PacketType.DUPLICATE_USERNAME, len(message))
        conn.socket.sendall(header + message)
        logging.warning(f'{conn.addr[0]}:{conn.addr[1]} notified of'
                        f' duplicate username, and user list sent')

    def process_message_packet(self, conn: ClientConnection,
                               recipient: [str], message: str):
        logging.info(f'Message received from {conn.username}: "{message}"')

        message = message.encode()
        header = encode_header(PacketType.IN_MESSAGE,
                               len(message), sender=conn.username)

        if recipient:
            self.unicast(header + message, recipient)
        else:
            self.broadcast(header + message, exclude=[conn.username])

    def process_file_list_request(self, conn: ClientConnection):
        logging.info(f'List of available files requested by {conn.username}')

        try:
            with os.scandir(self.files_path) as entries:
                files = [f'|-- {e.name}\n' for e in entries if e.is_file()]
        except FileNotFoundError:
            logging.warning(f'No files found on server')
            files = []

        message = f'download\n{"".join(files)}'.encode()
        header = encode_header(PacketType.FILE_LIST, len(message))
        conn.socket.sendall(header + message)
        logging.info(f'Available file list sent to {conn.username}')

    def process_download_request(self, conn: ClientConnection, filename: str):
        logging.info(f'{conn.username} requested to download {filename}')
        filepath = f'{self.files_path}/{filename}'
        try:
            with open(filepath, 'rb') as f:
                file = f.read()
        except FileNotFoundError:
            logging.error(f'File not found: "{filepath}"')
            return

        header = encode_header(PacketType.DOWNLOAD,
                               len(file), filename=filename)
        logging.info(f'Sending {filename} to {conn.username}')
        conn.socket.sendall(header + file)
        logging.info(f'Successfully sent {filename} to {conn.username}')

    def broadcast(self, data: bytes, exclude: list[str] = []):
        for conn in self.connections:
            if conn.username in exclude:
                continue
            conn.socket.sendall(data)
            logging.info(f'Packet sent to {conn.username}:'
                         f' "{data[HEADER_SIZE:].decode()}"')

    def unicast(self, data: bytes, recipient: str):
        for conn in self.connections:
            if conn.username == recipient:
                conn.socket.sendall(data)
                logging.info(f'Packet sent to {recipient}:'
                             f' "{data[HEADER_SIZE:].decode()}"')
            else:
                logging.warning(f'{recipient} is not currently connected')
                # TODO: Notify user that recipient doesn't exist

    def get_conn_by_socket(self, socket: socket.socket):
        for conn in self.connections:
            if conn.socket == socket:
                return conn

        logging.warning(f'Could not find socket in current connections')
        return None

    def get_connected_users(self):
        return [conn.username for conn in self.connections if conn.username]

    def close_conn(self, conn: ClientConnection):
        if conn.socket.fileno() != -1:
            conn.socket.shutdown(socket.SHUT_RDWR)
            conn.socket.close()

        logging.info(f'{conn.username} disconnected')

        message = f'{conn.username} has left the chat'.encode()
        header = encode_header(PacketType.ANNOUNCEMENT, len(message))
        self.broadcast(header + message, exclude=[conn.username])

        self.connections.remove(conn)
        logging.info(f'Removed {conn.username} from current connections')

    def close(self):
        logging.info(f'Server closing')
        sys.exit(0)


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
