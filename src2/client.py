# Standard Library Imports
import os
import sys
import socket
import threading
import time

# Local Imports
from packet_type import PacketType
from packet import (
    HEADER_SIZE,
    encode_header,
    decode_header,
    recv_generator
)


class Client:
    def __init__(self, username: str, hostname: str, port: int):
        self.username = username
        self.server_hostname = hostname
        self.server_port = port

        self.is_active = False
        self.requested_disconnect = False
        self.save_directory = f'{username}/'

    def start(self):
        # Setup socket
        print(f"Connecting to {self.server_hostname}:{self.server_port}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_hostname, self.server_port))
        self.is_active = True

        # Start a new thread to handle communication with the server
        server_thread = threading.Thread(target=self.handle_server_response)
        server_thread.daemon = True
        server_thread.start()

        header = encode_header(PacketType.METADATA, 0, username=username)
        self.socket.sendall(header)

        self.handle_cli_input()

    def handle_server_response(self):
        while self.is_active:
            data = self.socket.recv(HEADER_SIZE)
            if not data:
                continue

            expected_type, expected_size, params = decode_header(data)

            if expected_type == PacketType.DOWNLOAD:
                print('test')
                datastream = recv_generator(self.socket, expected_size)

                if not os.path.exists(self.save_directory):
                    os.makedirs(self.save_directory)

                download_path = self.save_directory + params.get('filename')
                print(f"File will be saved to: {download_path}")

                with open(download_path, 'wb') as file:
                    for file_data in datastream:
                        file.write(file_data)

                print(f"File saved to: {download_path}")
                continue

            message = self.socket.recv(expected_size)

            match expected_type:
                case PacketType.ANNOUNCEMENT:
                    self.process_announcement(message.decode())

    def process_in_message(self):
        pass

    def process_announcement(self, message):
        print(f'{message}')
        pass

    def process_duplicate_username(self):
        pass

    def process_file_list(self):
        pass

    def process_download(self):
        pass

    def handle_cli_input(self):
        while True:
            try:
                user_input = str(input()).rstrip()
            except KeyboardInterrupt as e:
                self.close()

            match user_input.split(maxsplit=2):
                case ['/disconnect']:
                    self.close()
                case ['/msg', username, user_input]:
                    # Direct message a specific client
                    if username == self.username:
                        print(f'Select someone other than yourself to directly message')
                        return
                    
                    message = user_input.encode()

                    header = encode_header(PacketType.OUT_MESSAGE, len(message), recipient=username)

                    self.socket.sendall(header + message)
                case ['/list_files']:
                    # Request a list of all available files
                    header = encode_header(PacketType.FILE_LIST_REQUEST, 0)
                    self.socket.sendall(header)
                case ['/download', filename]:
                    # Request to download a certain file
                    header = encode_header(PacketType.DOWNLOAD_REQUEST, 0, filename=filename)
                    self.socket.sendall(header)
                case _:
                    # Send message to everyone
                    message = user_input.encode()

                    header = encode_header(PacketType.OUT_MESSAGE, len(message))
                    self.socket.sendall(header + message)

    def close(self):
        print('Disconnecting from server')
        self.socket.close()
        sys.exit()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python client.py [username] [hostname] [port]")
        sys.exit(1)

    username = sys.argv[1]
    hostname = sys.argv[2]

    try:
        port = int(sys.argv[3])
    except ValueError:
        print("Invalid port number. Port must be an integer.")
        sys.exit(1)

    client = Client(username, hostname, port)
    client.start()
