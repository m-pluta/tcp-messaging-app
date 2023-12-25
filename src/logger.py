# Standard Library Imports
import logging
from enum import Enum


class LogEvent(Enum):
    # Enums for all types of logging events that could occur
    SERVER_INIT_START = 1
    SERVER_STARTED = 2
    SERVER_LISTENING = 3
    SERVER_CLOSE = 4
    USER_CONNECT = 5
    USER_THREAD_STARTED = 6
    USER_DISCONNECT = 7
    PACKET_RECEIVED = 8
    PACKET_SENT = 9
    FILE_LIST_REQUEST = 10
    DOWNLOAD_REQUEST = 11


class Logger:
    def __init__(self, log_filepath: str):
        # Setup log file
        self.log_filepath = log_filepath

        # Setup logger and formatting
        self.logger = logging.getLogger('my_logger')
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')

        # File Handler for writing to .log file
        file_handler = logging.FileHandler(log_filepath)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Console handler for writing to the console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)


    def log(self, event_type: LogEvent, kwargs: dict):
        # Unpack kwargs into local variables
        port = kwargs.get('port', None)
        ip_address = kwargs.get('ip_address', None)
        client_port = kwargs.get('client_port', None)
        username = kwargs.get('username', None)
        content = kwargs.get('content', None)
        filename = kwargs.get('filename', None)

        # Each LogEvent type has an associated message format
        log_messages = {
            LogEvent.SERVER_INIT_START: (
                f'Server starting on port {port}'),
            LogEvent.SERVER_STARTED: (
                f'Server started on port {port}'),
            LogEvent.SERVER_LISTENING: (
                f'Server listening on port {port}'),
            LogEvent.SERVER_CLOSE: (
                f'Server closing'),
            LogEvent.USER_CONNECT: (
                f'New client connection: {ip_address}:{client_port}'),
            LogEvent.USER_THREAD_STARTED: (
                f'Client thread started for {ip_address}:{client_port}'),
            LogEvent.USER_DISCONNECT: (
                f'Client {username} disconnected'),
            LogEvent.PACKET_RECEIVED: (
                f'Packet received from {username}: "{content}"'),
            LogEvent.PACKET_SENT: (
                f'Packet send to {username}: "{content}"'),
            LogEvent.FILE_LIST_REQUEST: (
                f'List of available files requested by {username}'),
            LogEvent.DOWNLOAD_REQUEST: (
                f'Client {username} requested to download {filename}'),
        }

        self.logger.info(log_messages.get(event_type, None)) 
