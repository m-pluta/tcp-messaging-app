# Standard Library Imports
import sys
import socket
import threading
import time

# Local Imports
from packet_type import PacketType
from packet import (
    HEADER_SIZE,
    encode_header,
    decode_header
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

        self.handle_cli_input()

    def handle_server_response(self):
        while True:
            print('From server')
            time.sleep(10)

    def process_in_message(self):
        pass

    def process_announcement(self):
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
                user_input = str(input())
            except KeyboardInterrupt as e:
                self.close()
                
            self.socket.sendall(user_input.encode())

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
