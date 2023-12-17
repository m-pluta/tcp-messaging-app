# Standard Library Imports
import sys
import socket
import uuid
import threading
import os

# Local Imports
from logger import (
    Logger,
    LogEvent,
)
from packet import (
    Packet,
    MessagePacket,
    AnnouncementPacket,
)


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
        self.files_path = 'files'
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
                    self.process_metadata_packet(packet, conn)
                case 'message':
                    self.process_message_packet(packet, conn)
                case 'file_list_request':
                    self.process_file_list_request_packet(conn)
                case 'download_request':
                    self.process_download_request_packet(packet, conn)

        self.close_client(conn.uuid)

    def process_metadata_packet(self, incoming_packet, client_conn):
        # Extract username from metadata
        username = incoming_packet.get('username')
        self.logger.log(
            LogEvent.PACKET_RECEIVED,
            uuid=client_conn.uuid,
            content=username
        )
        client_conn.username = username

        # Send announcement to all other clients
        packet = AnnouncementPacket(
            content=(
                f'{username} has joined the chat!'
            )
        )
        self.broadcast_new(None, packet, exclude=[client_conn.uuid])

    def process_message_packet(self, incoming_packet, client_conn):
        packet_content = incoming_packet.get('content')
        self.logger.log(
            LogEvent.PACKET_RECEIVED,
            uuid=client_conn.uuid,
            content=packet_content
        )

        recipient_username = incoming_packet.get('recipient')
        recipient_uuid = self.get_uuid(recipient_username)

        packet = MessagePacket(
            sender=None, recipient=None,
            content=packet_content
        )

        if recipient_uuid:
            self.unicast_new(client_conn.uuid, recipient_uuid, packet)
        else:
            self.broadcast_new(client_conn.uuid, packet)

    def process_file_list_request_packet(self, client_conn):
        self.logger.log(
            LogEvent.FILE_LIST_REQUEST,
            uuid=client_conn.uuid
        )
        try:
            with os.scandir(self.files_path) as entries:
                files = [e.name for e in entries if e.is_file()]
        except FileNotFoundError:
            files = []

        if files:
            file_list = " ".join(files)

            packet = MessagePacket(
                sender=None, recipient=None,
                content=file_list
            )

            self.unicast_new(None, client_conn.uuid, packet)
        else:
            print(f'No files found in {self.files_path}')

    def process_download_request_packet(self, incoming_packet, client_conn):
        filename = incoming_packet.get('filename')
        self.logger.log(
            LogEvent.DOWNLOAD_REQUEST,
            filename=filename,
            uuid=client_conn.uuid
        )

    def unicast_new(self, sender_uuid, recipient_uuid, packet: Packet):
        if recipient_uuid in self.connections:
            packet.sender = self.get_username(sender_uuid)
            packet.recipient = self.get_username(recipient_uuid)

            recipient_socket = self.connections[recipient_uuid].socket
            recipient_socket.send(packet.to_json().encode())

            self.logger.log(
                LogEvent.PACKET_SENT,
                uuid=recipient_uuid,
                content=packet.content
            )

    def broadcast_new(self, sender_uuid, packet: Packet, exclude=[]):
        sender_username = self.get_username(sender_uuid)
        packet.sender = sender_username

        for recipient_uuid, recipient_info in self.connections.items():
            if recipient_uuid in ([sender_uuid] + exclude):
                continue

            packet.recipient = recipient_info.username
            print(packet)

            recipient_info.socket.send(packet.to_json().encode())

            self.logger.log(
                LogEvent.PACKET_SENT,
                uuid=recipient_uuid,
                content=packet.content
            )

    def get_username(self, uuid):
        if uuid is None:
            return None
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
