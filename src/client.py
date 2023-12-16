# Standard Library Imports
import select
import sys
import socket

# Local Imports
from packet import Packet, MetadataPacket, MessagePacket


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

        inputs = [clientSocket, sys.stdin]
        while True:
            # Monitor for readability
            readable, _, _ = select.select(inputs, [], [])

            for sock in readable:
                if sock is clientSocket:
                    # Receive response
                    data = clientSocket.recv(1024).decode()

                    incoming_packet = Packet.loads(data)
                    print(f'{incoming_packet["sender"]}: '
                          f'{incoming_packet["content"]}')

                elif sock is sys.stdin:
                    # Read input from user
                    message = input()
                    match message.split(maxsplit=2):
                        case ['/disconnect']:
                            break
                        case ['/msg', username, message]:
                            # Send data to server
                            packet = MessagePacket(sender=self.username,
                                                   recipient=username,
                                                   content=message)
                            clientSocket.send(packet.to_json().encode())
                        case _:
                            # Send data to server
                            packet = MessagePacket(sender=self.username,
                                                   recipient=None,
                                                   content=message)
                            clientSocket.send(packet.to_json().encode())

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
