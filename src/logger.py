# Standard Library Imports
from enum import Enum
import datetime


class LogEvent(Enum):
    # Enums for all types of logging events that can occur
    SERVER_INIT_START = 1
    SERVER_STARTED = 2
    SERVER_LISTENING = 3
    SERVER_CLOSE = 4
    SERVER_BIND_ERROR = 5

    USER_CONNECT = 6
    USER_THREAD_STARTED = 7
    USER_DISCONNECT = 8

    PACKET_RECEIVED = 9
    PACKET_SENT = 10

    FILE_LIST_REQUEST = 11
    DOWNLOAD_REQUEST = 12

    def get_max_length():
        return max([len(event.name) for event in LogEvent])


class Logger:
    def __init__(self, log_filepath: str):
        self.log_filepath = log_filepath
        self.clear()
        self.write_log_file_header()

    def log(self, event_type, **kwargs):
        timestamp = self.get_formatted_timestamp()
        log_content = self.get_log_content(event_type, kwargs)
        max_length = LogEvent.get_max_length()

        log_entry = (
            f'{timestamp} | '
            f'{event_type.name.ljust(max_length)} | '
            f'{log_content}'
        )
        print(log_content)

        with open(self.log_filepath, 'a') as file:
            file.write(f'{log_entry}\n')

    def get_log_content(self, event_type, kwargs):
        # Unpack kwargs into local variables
        port = kwargs.get('port', None)
        delay = kwargs.get('delay', None)
        username = kwargs.get('username', None)
        ip_address = kwargs.get('ip_address', None)
        client_port = kwargs.get('client_port', None)
        content = kwargs.get('content', None)
        filename = kwargs.get('filename', None)

        log_messages = {
            LogEvent.SERVER_INIT_START: (
                f'Server starting on port {port}'
            ),
            LogEvent.SERVER_STARTED: (
                f'Server started on port {port}'
            ),
            LogEvent.SERVER_LISTENING: (
                f'Server listening on port {port}'
            ),
            LogEvent.SERVER_CLOSE: (
                'Server shutting down'
            ),
            LogEvent.SERVER_BIND_ERROR: (
                f'Server encounted an error when binding. Port already in use'
            ),
            LogEvent.USER_CONNECT: (
                f'New client connection: {ip_address}:{client_port}'
            ),
            LogEvent.USER_THREAD_STARTED: (
                f'Client thread started for {ip_address}:{client_port}'
            ),
            LogEvent.USER_DISCONNECT: (
                f'Client {username} disconnected'
            ),
            LogEvent.PACKET_RECEIVED: (
                f'Packet received from {username}, Content: {content}'
            ),
            LogEvent.PACKET_SENT: (
                f'Packet sent to {username}, Content: {content}'
            ),
            LogEvent.FILE_LIST_REQUEST: (
                f'List of available files requested by {username}'
            ),
            LogEvent.DOWNLOAD_REQUEST: (
                f'Client {username} requested to download {filename}'
            )
        }

        return log_messages.get(event_type, None)

    def clear(self):
        # Open and close file in write mode to clear
        with open(self.log_filepath, 'w'):
            pass

    def write_log_file_header(self):
        timestamp_length = len(self.get_formatted_timestamp())
        max_length = LogEvent.get_max_length()

        # Write header of log file
        with open(self.log_filepath, 'a') as file:
            file.write(
                f'{"Timestamp".ljust(timestamp_length)} | '
                f'{"Event Type".ljust(max_length)} | '
                f'{"Event details"}\n'
            )
            file.write(f'{"".join(["-"] * 120)}\n')

    def get_formatted_timestamp(self):
        raw_ts = datetime.datetime.now()
        return (f'{raw_ts.strftime("[%d/%b/%Y %H:%M:%S.")}'
                f'{raw_ts.microsecond // 1000:03d}]')
