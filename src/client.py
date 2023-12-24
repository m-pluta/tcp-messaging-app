# Standard Library Imports
import os
import select
import sys
import socket

# Local Imports
from packet import (
    PACKET_SIZE,
    HEADER_SIZE,
    ENCODING,
    PacketType,
    HeaderPacket,
    MetadataPacket,
    OutMessagePacket,
    FileListRequestPacket,
    DownloadRequestPacket)

from utility import (
    recv_full,
    recv_generator,
    extract_from_delimiter)


class Client:
    def __init__(self, username, hostname, port):
        self.username = username
        self.server_hostname = hostname
        self.server_port = port

        self.is_active = True
        self.requested_disconnect = False
        self.save_directory = f'{username}/'

    def send_packet(self, packet):
        bytes = packet.to_bytes()
        self.socket.sendall(bytes)

    def connect(self):
        # Setup socket
        print(f"Connecting to {self.server_hostname}:{self.server_port}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_hostname, self.server_port))

        # Send metadata to server before beginning main transmission
        packet = MetadataPacket(content=self.username)
        self.send_packet(packet)

        inputs = [self.socket, sys.stdin]
        while self.is_active:
            # Monitor for readability
            readable, _, _ = select.select(inputs, [], [])

            for sock in readable:
                if sock is self.socket:
                    self.handle_server_response()

                elif sock is sys.stdin:
                    self.handle_user_command()

                if self.requested_disconnect:
                    self.is_active = False
                    break

        self.socket.close()

    def handle_server_response(self):
        encoded_header = self.socket.recv(HEADER_SIZE)
        header: dict = HeaderPacket.decode(encoded_header)

        expected_size = header.get('size', 0)

        match header.get('type'):
            case PacketType.IN_MESSAGE:
                sender = self.socket.recv(PACKET_SIZE).decode(ENCODING)
                sender = extract_from_delimiter(sender)
                expected_size -= PACKET_SIZE

                content = recv_full(self.socket, expected_size)
                self.process_in_message(content, sender)
            case PacketType.ANNOUNCEMENT:
                content = recv_full(self.socket, expected_size)
                self.process_announcement(content)
            case PacketType.DUPLICATE_USERNAME:
                content = recv_full(self.socket, expected_size)
                self.process_duplicate_username(content)
            case PacketType.FILE_LIST:
                content = recv_full(self.socket, expected_size)
                self.process_file_list(content)
            case PacketType.DOWNLOAD:
                filename = self.socket.recv(PACKET_SIZE).decode(ENCODING)
                filename = extract_from_delimiter(filename)
                expected_size -= PACKET_SIZE

                datastream = recv_generator(self.socket, expected_size)
                self.process_download(datastream, filename)

    def process_in_message(self, data, sender):
        content = data.decode(ENCODING)
        if sender:
            print(f'{sender}: {content}')
        else:
            print(f'{content}')

    def process_announcement(self, data):
        content = data.decode(ENCODING)
        print(f'{content}')

    def process_duplicate_username(self, data):
        content = data.decode(ENCODING)
        print('This username is already taken')
        print(f'Current users connected to the server: {content}')

        new_username = input('Enter a new username: ')

        packet = MetadataPacket(new_username)
        self.send_packet(packet)

        self.username = new_username

    def process_file_list(self, data):
        print(f'Available files:\n{data.decode(ENCODING)}')

    def process_download(self, datastream, filename):
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)

        download_path = self.save_directory + filename
        print(f"File will be saved to: {download_path}")

        with open(download_path, 'wb') as file:
            for file_data in datastream:
                file.write(file_data)

        print(f"File saved to: {download_path}")

    def handle_user_command(self):
        # Read input from user
        user_input = input().rstrip()
        if not user_input:
            return

        match user_input.split(maxsplit=2):
            case ['/disconnect']:
                self.requested_disconnect = True
            case ['/msg', username, user_input]:
                # Direct message a specific client
                if username == self.username:
                    print(f'Select someone other than '
                          f'yourself to directly message')
                    return

                packet = OutMessagePacket(user_input, username)
                self.send_packet(packet)
            case ['/list_files']:
                # Request a list of all available files
                packet = FileListRequestPacket()
                self.send_packet(packet)
            case ['/download', filename]:
                # Request to download a certain file
                packet = DownloadRequestPacket(filename)
                self.send_packet(packet)
            case _:
                # Send message to everyone
                packet = OutMessagePacket(user_input, None)
                self.send_packet(packet)


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
    client.connect()
