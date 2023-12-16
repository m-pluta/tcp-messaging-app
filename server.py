import sys
from enum import Enum
import datetime
import socket
import uuid
import threading

class LogEvent(Enum):
    # Enums for all types of logging events that can occur
    SERVER_INIT_START = 1
    SERVER_STARTED = 2
    SERVER_LISTENING = 3
    SERVER_CLOSE = 4
    SERVER_ERROR = 5
    USER_CONNECT = 6
    USER_DISCONNECT = 7
    PACKET_RECEIVED = 8
    PACKET_SENT = 9
    USER_THREAD_STARTED = 10
    USER_DOWNLOAD_REQUEST = 11

    def getMaxEventNameLength():
        return max([len(event.name) for event in LogEvent])

class Logger:
    def __init__(self, log_filepath: str):
        # Clear current state of logfile
        self.log_filepath = log_filepath
        self.clear()

        # Write header of log file
        with open(self.log_filepath, 'a') as file:
            file.write(f'{"Timestamp".ljust(len(self.getFormattedTimestamp()))} | {"Event Type".ljust(LogEvent.getMaxEventNameLength())} | {"Event details"}\n')
            file.write(f'{"".join(["-"] * 120)}\n')

    def log(self, event_type, log_content):
        ts = self.getFormattedTimestamp()
        log_entry = f"{ts} | {event_type.name.ljust(LogEvent.getMaxEventNameLength())} | {log_content}"
        print(log_entry)
        with open(self.log_filepath, 'a') as file:
            file.write(f'{log_entry}\n')

    def clear(self):
        # Open and close file in write mode to clear
        with open(self.log_filepath, 'w'):
            pass

    def getRawTimestamp(self):
        return datetime.datetime.now()
    
    def getFormattedTimestamp(self):
        raw_ts = self.getRawTimestamp()
        return raw_ts.strftime('[%d/%b/%Y %H:%M:%S.') + f"{raw_ts.microsecond // 1000:03d}]"

class ClientConnection:
    nextID = 0

    def __init__(self, socket, address):
        self.socket = socket
        self.ip_address = address[0]
        self.port = address[1]
        self.uuid = ClientConnection.nextID
        ClientConnection.nextID += 1
        
    def generateUUID(self):
        return str(uuid.uuid4())

class Server:
    def __init__(self, port):
        # Init key variables and create logger
        self.port = port
        self.logger = Logger('./server.log')
        self.currentConnections = {}

    def start(self):
        # Begin starting the server
        self.logger.log(LogEvent.SERVER_INIT_START, f'Server starting on port {self.port}')

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.socket.bind(("", self.port))
        self.socket.listen(1)
        self.is_running = True
        self.logger.log(LogEvent.SERVER_STARTED, f'Server started on port {self.port}')

        self.listen()

    def listen(self):
        self.logger.log(LogEvent.SERVER_LISTENING, f'Server started listening on port {self.port}')

        while self.is_running: 
            # New client tried to establish a connection
            cSocket, addr = self.socket.accept()
            conn = ClientConnection(cSocket, addr)
            self.currentConnections[conn.uuid] = conn
            self.logger.log(LogEvent.USER_CONNECT, f'New client connection: uuid: {conn.uuid}, ip_address: {conn.ip_address}, client_port: {conn.port}')

            # Start a new thread to handle communication with the new client
            cThread = threading.Thread(target=self.handleClient, args=(conn,))
            cThread.start()
            self.logger.log(LogEvent.USER_THREAD_STARTED, f'Client thread started for uuid: {conn.uuid}')


    def handleClient(self, conn):
        while True:
            data = conn.socket.recv(1024)
            if not data:
                break
            message = data.decode()
            self.logger.log(LogEvent.PACKET_RECEIVED, f'Packet received from uuid {conn.uuid}, Content: {message}')

            modifiedMessage = message.upper()
            conn.socket.send(modifiedMessage.encode())
            self.logger.log(LogEvent.PACKET_SENT, f'Packet send to uuid {conn.uuid}, Content: {modifiedMessage}')

        self.closeClient(conn.uuid)

    def closeClient(self, uuid):
        self.logger.log(LogEvent.USER_DISCONNECT, f'Client disconnected: uuid: {uuid}')
        self.currentConnections[uuid].socket.close()
        del self.currentConnections[uuid]

    def closeServer(self):
        self.is_running = False
        self.socket.close()
        self.logger.log(LogEvent.SERVER_CLOSE, 'Server shutting down')





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
