# Standard Library Imports
import os
import select
import sys
import socket

# External libraries
import tkinter as tk
from tkinter import filedialog

# Local Imports
from packet import (
    ENCODING,
    HEADER_SIZE,
    PACKET_SIZE,
    PacketType,
    HeaderPacket,
    MetadataPacket,
    OutMessagePacket,
    FileListRequestPacket,
    DownloadRequestPacket,
)
from utility import recv_to_buffer, extract_delimiter


class Client:
    def __init__(self, username, hostname, port):
        self.username = username
        self.server_hostname = hostname
        self.server_port = port

        self.is_active = True
        self.requested_disconnect = False
        self.save_directory = f'{username}/'

    def connect(self):
        # Setup socket
        print(f"Connecting to {self.server_hostname}:{self.server_port}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_hostname, self.server_port))

        # Send metadata to server before beginning main transmission
        packet = MetadataPacket(content=self.username)
        self.socket.sendall(packet.to_bytes())

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
        header_data = self.socket.recv(HEADER_SIZE)
        print(f'Header length: {len(header_data)}')
        header: dict = HeaderPacket.decode(header_data)

        print(header.get('size', 0))
        content_data = recv_to_buffer(self.socket, 
                                      header.get('size', 0))
        print(f'Content data bytes: {len(content_data)}')

        match header.get('type'):
            case PacketType.IN_MESSAGE:
                sender = extract_delimiter(content_data[:PACKET_SIZE].decode(ENCODING))
                content = content_data[PACKET_SIZE:].decode(ENCODING)
                if sender:
                    print(f'{sender}: {content}')
                else:
                    print(f'{content}')
            case PacketType.ANNOUNCEMENT:
                content = content_data.decode(ENCODING)
                print(f'{content}')
            case PacketType.DUPLICATE_USERNAME:
                content = content_data.decode(ENCODING)
                print('This username is already taken')
                print(f'Current users connected to the server: {content}')

                newUsername = input('Enter a new username: ')

                packet = MetadataPacket(username=newUsername)
                self.socket.sendall(packet.to_bytes())

                self.username = newUsername
            case PacketType.DOWNLOAD:
                if not os.path.exists(self.save_directory):
                    os.makedirs(self.save_directory)

                target_filename = extract_delimiter(content_data[:PACKET_SIZE].decode(ENCODING))
                file_data = content_data[PACKET_SIZE:]

                print(target_filename)

                download_path = self.save_directory + target_filename
                print(f"File will be saved to: {download_path}")

                with open(download_path, 'wb') as file:
                    file.write(file_data)

    def handle_user_command(self):
        # Read input from user
        message = input().rstrip()
        if not message:
            return

        match message.split(maxsplit=2):
            case ['/disconnect']:
                self.requested_disconnect = True
            case ['/msg', username, message]:
                # Direct message a specific client
                if username == self.username:
                    print('Select someone other than yourself to directly message')
                    return
                
                packet = OutMessagePacket(content=message, recipient=username)
                self.socket.sendall(packet.to_bytes())
            case ['/list_files']:
                # Request a list of all available files
                packet = FileListRequestPacket()
                self.socket.sendall(packet.to_bytes())
            case ['/download', filename]:
                # Request to download a certain file
                packet = DownloadRequestPacket(content=filename)
                self.socket.sendall(packet.to_bytes())
            case _:
                # Send message to everyone
                packet = OutMessagePacket(content=message, recipient=None)
                self.socket.sendall(packet.to_bytes())


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
