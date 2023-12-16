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
