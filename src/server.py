# Standard Library Imports
import sys
import socket
import uuid
import threading

# Local Imports
from logger import Logger, LogEvent
from packet import Packet, MessagePacket


class ClientConnection:
    next_id = 0

    def __init__(self, socket, address):
        self.socket = socket
        self.ip_address = address[0]
        self.port = address[1]
        self.uuid = f'uuid-{ClientConnection.next_id}'
        ClientConnection.next_id += 1

    # TODO: replace ids with uuid
    def generate_uuid(self):
        return str(uuid.uuid4())


class Server:
    def __init__(self, port):
        # Init key variables and create logger
        self.port = port
        self.logger = Logger('./server.log')
        self.connections = {}

    def start(self):
        # Begin starting the server
        self.logger.log(
            LogEvent.SERVER_INIT_START,
            port=self.port
        )

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("", self.port))
        self.socket.listen(1)
        self.is_running = True

        self.logger.log(
            LogEvent.SERVER_STARTED,
            port=self.port
        )

        self.listen()

    def listen(self):
        self.logger.log(
            LogEvent.SERVER_LISTENING,
            port=self.port
        )

        while self.is_running:
            # New client tries to establish a connection
            client_socket, addr = self.socket.accept()
            conn = ClientConnection(client_socket, addr)
            self.connections[conn.uuid] = conn
            self.logger.log(
                LogEvent.USER_CONNECT,
                uuid=conn.uuid,
                ip_address=conn.ip_address,
                client_port=conn.port
            )

            # Start a new thread to handle communication with the new client
            client_thread = threading.Thread(
                target=self.handle_client,
                args=(conn,)
            )
            client_thread.start()
            self.logger.log(
                LogEvent.USER_THREAD_STARTED,
                uuid=conn.uuid
            )

        self.close_server()

    def handle_client(self, conn):
        while True:
            # Check if client disconnected
            data = conn.socket.recv(1024)
            if not data:
                break

            # Handle client sending a packet to the server
            packet = Packet.loads(data.decode())

            match (packet.get('type')):
                case 'metadata':
                    username = packet.get('username')
                    self.logger.log(
                        LogEvent.PACKET_RECEIVED,
                        uuid=conn.uuid,
                        content=username
                    )
                    conn.username = username
                case 'message':
                    packet_content = packet.get('content')

                    self.logger.log(
                        LogEvent.PACKET_RECEIVED,
                        uuid=conn.uuid,
                        content=packet_content
                    )

                    if recipient_username := packet.get('recipient'):

                        recipient_uuid = self.get_uuid(recipient_username)
                        self.unicast(conn.uuid, recipient_uuid, packet_content)

                    else:
                        self.broadcast(conn.uuid, packet_content)
                case 'file_list_request':
                    pass
                case 'file_request':
                    pass

        self.close_client(conn.uuid)

    def unicast(self, sender_uuid, recipient_uuid, message):
        if recipient_uuid in self.connections:

            sender_username = self.get_username(sender_uuid)
            recipient_username = self.get_username(recipient_uuid)

            packet = MessagePacket(
                sender=sender_username,
                recipient=recipient_username,
                content=message
            )

            recipient_socket = self.connections[recipient_uuid].socket
            recipient_socket.send(packet.to_json().encode())

            self.logger.log(
                LogEvent.PACKET_SENT,
                uuid=recipient_uuid,
                content=message
            )

    def broadcast(self, sender_uuid, message):
        sender_username = self.get_username(sender_uuid)

        for recipient_uuid, recipient_info in self.connections.items():
            if recipient_uuid == sender_uuid:
                continue

            recipient_username = recipient_info.username

            message_packet = MessagePacket(
                sender=sender_username,
                recipient=recipient_username,
                content=message
            )

            recipient_info.socket.send(message_packet.to_json().encode())

            self.logger.log(
                LogEvent.PACKET_SENT,
                uuid=recipient_uuid,
                content=message
            )

    def get_username(self, uuid):
        if uuid is None:
            return 'SERVER'
        try:
            return self.connections[uuid].username
        except KeyError:
            print(f'{uuid} does not exist')

    def get_uuid(self, username):
        for conn_uuid, conn_info in self.connections.items():
            if conn_info.username == username:
                return conn_uuid
        return None

    def close_client(self, client_uuid):
        if client_uuid in self.connections:
            self.connections[client_uuid].socket.close()
            del self.connections[client_uuid]
            self.logger.log(
                LogEvent.USER_DISCONNECT,
                uuid=client_uuid
            )

    def close_server(self):
        self.is_running = False
        self.socket.close()
        self.logger.log(
            LogEvent.SERVER_CLOSE
        )


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
