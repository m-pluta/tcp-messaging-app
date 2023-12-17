# Standard Library Imports
from enum import Enum
import datetime


class LogEvent(Enum):
    # Enums for all types of logging events that can occur
    SERVER_INIT_START = 1
    SERVER_STARTED = 2
    SERVER_LISTENING = 3
    SERVER_CLOSE = 4
    SERVER_ERROR = 5

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
        # Clear current state of logfile
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

        with open(self.log_filepath, 'a') as file:
            file.write(f'{log_entry}\n')

    def get_log_content(self, event_type, kwargs):
        # Unpack kwargs into local variables
        port = kwargs.get('port')
        uuid = kwargs.get('uuid')
        ip_address = kwargs.get('ip_address')
        client_port = kwargs.get('client_port')
        content = kwargs.get('content')
        filename = kwargs.get('filename')

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
            LogEvent.SERVER_ERROR: (
                'Server encounted an error'
            ),
            LogEvent.USER_CONNECT: (
                f'New client connection: '
                f'{ip_address}: {client_port}'
            ),
            LogEvent.USER_THREAD_STARTED: (
                f'Client thread started for uuid: {uuid}'
            ),
            LogEvent.USER_DISCONNECT: (
                f'Client disconnected: uuid: {uuid}'
            ),
            LogEvent.PACKET_RECEIVED: (
                f'Packet received: '
                f'uuid: {uuid}, '
                f'Content: {content}'
            ),
            LogEvent.PACKET_SENT: (
                f'Packet sent: '
                f'uuid: {uuid}, '
                f'Content: {content}'
            ),
            LogEvent.FILE_LIST_REQUEST: (
                f'Available files requested by '
                f'uuid: {uuid}'
            ),
            LogEvent.DOWNLOAD_REQUEST: (
                f'{filename} requested for download by '
                f'uuid: {uuid}'
            )
        }

        return log_messages.get(event_type, None)

    def clear(self):
        # Open and close file in write mode to clear
        with open(self.log_filepath, 'w'):
            pass

    def write_log_file_header(self):
        ts_length = len(self.get_formatted_timestamp())
        max_length = LogEvent.get_max_length()

        # Write header of log file
        with open(self.log_filepath, 'a') as file:
            file.write(
                f'{"Timestamp".ljust(ts_length)} | '
                f'{"Event Type".ljust(max_length)} | '
                f'{"Event details"}\n'
            )
            file.write(f'{"".join(["-"] * 120)}\n')

    def get_raw_timestamp(self):
        return datetime.datetime.now()

    def get_formatted_timestamp(self):
        raw_ts = self.get_raw_timestamp()
        return (f'{raw_ts.strftime("[%d/%b/%Y %H:%M:%S.")}'
                f'{raw_ts.microsecond // 1000:03d}]')
