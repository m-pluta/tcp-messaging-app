# Standard Library Imports
import select
import sys
import socket

# External libraries
import tkinter as tk
from tkinter import filedialog

# Local Imports
from packet import (
    Packet,
    MetadataPacket,
    MessagePacket,
    FileListRequestPacket,
    FileRequestPacket
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
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.server_hostname, self.server_port))

        # Send metadata to server before beginning main transmission
        metadata_packet = MetadataPacket(username=self.username)
        client_socket.send(metadata_packet.to_json().encode())

        inputs = [client_socket, sys.stdin]
        while self.is_active:
            # Monitor for readability
            readable, _, _ = select.select(inputs, [], [])

            for sock in readable:
                if sock is client_socket:
                    self.handle_server_response(client_socket)

                elif sock is sys.stdin:
                    self.hand_user_command(client_socket)

                if self.requested_disconnect:
                    self.is_active = False
                    break

        client_socket.close()

    def handle_server_response(self, client_socket):
        # Receive response
        data = client_socket.recv(1024).decode()

        incoming_packet = Packet.loads(data)
        print(
            f'{incoming_packet.get("sender")}: '
            f'{incoming_packet.get("content")}'
        )

    def hand_user_command(self, client_socket):
        # Read input from user
        message = input().rstrip()
        if not message:
            return

        match message.split(maxsplit=2):
            case ['/disconnect']:
                self.requested_disconnect = True
            case ['/msg', username, message]:
                # Send data to server
                packet = MessagePacket(
                    sender=self.username,
                    recipient=username,
                    content=message
                )
                client_socket.send(packet.to_json().encode())
            case ['/list_files']:
                # Send data to server
                packet = FileListRequestPacket()
                client_socket.send(packet.to_json().encode())
            case ['/download', filename]:
                # Create a Tkinter root window (it won't be shown)
                root = tk.Tk()
                root.withdraw()

                folder_path = filedialog.askdirectory()
                if folder_path:
                    print(f"Selected folder: {folder_path}")
                    self.download_path = folder_path
                    packet = FileRequestPacket(filename=filename)
                    client_socket.send(packet.to_json().encode())
                else:
                    print("No folder selected")

                root.destroy()

            case _:
                # Send data to server
                packet = MessagePacket(
                    sender=self.username,
                    recipient=None,
                    content=message
                )
                client_socket.send(packet.to_json().encode())


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
