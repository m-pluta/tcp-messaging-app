# Setup
import sys

# Packets
from packet import Packet, MetadataPacket, MessagePacket

# Main
import socket


class Client:
    def __init__(self, username, hostname, port):
        self.username = username
        self.serverHostname = hostname
        self.serverPort = port

    def connect(self):
        # Setup socket
        print(f"Connecting to {self.serverHostname}:{self.serverPort}")
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((self.serverHostname, self.serverPort))

        # Send metadata to server before beginning main transmission
        metadata_packet = MetadataPacket(username=self.username)
        clientSocket.send(metadata_packet.to_json().encode())

        while True:
            # Read input from user
            message = input("Input lowercase sentence: ")
            match message:
                case '/disconnect':
                    break

            # Send data to server
            outgoing_packet = MessagePacket(recipient='everyone',
                                            content=message)
            clientSocket.send(outgoing_packet.to_json().encode())

            # Receive response
            data = clientSocket.recv(1024).decode()

            incoming_packet = Packet.loads(data)
            print(f'Server: {incoming_packet["content"]}')

        clientSocket.close()


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
