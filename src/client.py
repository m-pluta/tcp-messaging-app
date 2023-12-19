# Standard Library Imports
import select
import sys
import socket

# External libraries
import tkinter as tk
from tkinter import filedialog

# Local Imports
from packet import (
    HEADER_SIZE,
    PacketType,
    Packet,
    MetadataPacket,
    OutMessagePacket,
    FileListRequestPacket,
    DownloadRequestPacket,
    send_packet
)


class Client:
    def __init__(self, username, hostname, port):
        self.username = username
        self.server_hostname = hostname
        self.server_port = port

        self.is_active = True
        self.requested_disconnect = False
        self.download_path = None

    def connect(self):
        # Setup socket
        print(f"Connecting to {self.server_hostname}:{self.server_port}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_hostname, self.server_port))

        # Send metadata to server before beginning main transmission
        metadata_packet = MetadataPacket(username=self.username)
        send_packet(self.socket, metadata_packet)

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
        # Receive response
        data = self.socket.recv(HEADER_SIZE).decode()
        header_packet = Packet.loads(data)

        if PacketType(header_packet.get('type')) == PacketType.HEADER:
            expected_size = header_packet.get('size')

            data = self.socket.recv(expected_size).decode()
            content_packet = Packet.loads(data)

            match PacketType(content_packet.get('type')):
                case PacketType.IN_MESSAGE:
                    sender = content_packet.get('sender')
                    content = content_packet.get('content')
                    if sender:
                        print(f'{sender}: {content}')
                    else:
                        print(f'{content}')
                case PacketType.ANNOUNCEMENT:
                    content = content_packet.get('content')
                    print(f'{content}')

    def handle_user_command(self):
        # Read input from user
        message = input().rstrip()
        if not message:
            return

        match message.split(maxsplit=2):
            case ['/disconnect']:
                self.requested_disconnect = True
            case ['/msg', username, message]:
                # Send data to server
                packet = OutMessagePacket(content=message, recipient=username)
                send_packet(self.socket, packet)
            case ['/list_files']:
                # Send data to server
                packet = FileListRequestPacket()
                send_packet(self.socket, packet)
            case ['/download', filename]:
                # Create a Tkinter root window (it won't be shown)
                root = tk.Tk()
                root.withdraw()

                folder_path = filedialog.askdirectory()
                if folder_path:
                    print(f"Selected folder: {folder_path}")
                    self.download_path = folder_path
                    packet = DownloadRequestPacket(filename=filename)
                    send_packet(self.socket, packet)
                else:
                    print("No folder selected")

                root.destroy()

            case _:
                # Send data to server
                packet = OutMessagePacket(content=message, recipient=None)
                send_packet(self.socket, packet)


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
