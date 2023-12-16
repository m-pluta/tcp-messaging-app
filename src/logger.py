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

        lenTimeStamp = len(self.getFormattedTimestamp())
        maxEventLength = LogEvent.getMaxEventNameLength()

        # Write header of log file
        with open(self.log_filepath, 'a') as file:
            file.write(f'{"Timestamp".ljust(lenTimeStamp)} | '
                       f'{"Event Type".ljust(maxEventLength)} | '
                       f'{"Event details"}\n')
            file.write(f'{"".join(["-"] * 120)}\n')

    def log(self, event_type, **kwargs):
        timestamp = self.getFormattedTimestamp()
        logContent = self.getLogContent(event_type, kwargs)
        maxEventLength = LogEvent.getMaxEventNameLength()
        log_entry = (f'{timestamp} | '
                     f'{event_type.name.ljust(maxEventLength)} | '
                     f'{logContent}')
        print(log_entry)
        with open(self.log_filepath, 'a') as file:
            file.write(f'{log_entry}\n')

    def getLogContent(self, event_type, kwargs):
        match (event_type):
            case LogEvent.SERVER_INIT_START:
                return f'Server starting on port {kwargs.get("port")}'

            case LogEvent.SERVER_STARTED:
                return f'Server started on port {kwargs.get("port")}'

            case LogEvent.SERVER_LISTENING:
                return f'Server started listening on port {kwargs.get("port")}'

            case LogEvent.USER_CONNECT:
                return (f'New client connection: '
                        f'uuid: {kwargs.get("uuid")}, '
                        f'ip_address: {kwargs.get("ip_address")}, '
                        f'client_port: {kwargs.get("clientPort")}')

            case LogEvent.USER_THREAD_STARTED:
                return f'Client thread started for uuid: {kwargs.get("uuid")}'

            case LogEvent.PACKET_RECEIVED:
                return (f'Packet received: '
                        f'uuid: {kwargs.get("uuid")}, '
                        f'Content: {kwargs.get("content")}')

            case LogEvent.PACKET_SENT:
                return (f'Packet sent:'
                        f'uuid: {kwargs.get("uuid")}, '
                        f'Content: {kwargs.get("content")}')

            case LogEvent.USER_DISCONNECT:
                return f'Client disconnected: uuid: {kwargs.get("uuid")}'

            case LogEvent.SERVER_CLOSE:
                return 'Server shutting down'

        return None

    def clear(self):
        # Open and close file in write mode to clear
        with open(self.log_filepath, 'w'):
            pass

    def getRawTimestamp(self):
        return datetime.datetime.now()

    def getFormattedTimestamp(self):
        raw_ts = self.getRawTimestamp()
        return (f'{raw_ts.strftime("[%d/%b/%Y %H:%M:%S.")}'
                f'{raw_ts.microsecond // 1000:03d}]')
