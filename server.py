import sys
from enum import Enum
import datetime

DEFAULT_HOSTNAME = '127.0.0.1'
DEFAULT_LOG_PATH = './server.log'

class LogEvent(Enum):
    SERVER_START = 1
    SERVER_CLOSE = 2
    SERVER_ERROR = 3
    USER_CONNECT = 4
    USER_DISCONNECT = 5
    USER_MESSAGE = 6
    USER_DOWNLOAD_REQUEST = 7

    def getMaxEventNameLength():
        return max([len(event.name) for event in LogEvent])

class Logger:
    def __init__(self, log_filepath: str):
        self.log_filepath = log_filepath
        self.clear()

    def log(self, event_type, log_content):
        ts = self.getFormattedTimestamp()
        log_entry = f"{ts} - {event_type.name.ljust(LogEvent.getMaxEventNameLength())}: {log_content}\n"
        with open(self.log_filepath, 'a') as file:
            file.write(log_entry)

    def clear(self):
        with open(self.log_filepath, 'w'):
            pass

    def getRawTimestamp(self):
        return datetime.datetime.now()
    
    def getFormattedTimestamp(self):
        raw_ts = self.getRawTimestamp()
        return raw_ts.strftime('[%d/%b/%Y %H:%M:%S.') + f"{raw_ts.microsecond // 1000:03d}]"

class Server:
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self.logger = Logger(DEFAULT_LOG_PATH)

    def start(self):
        print(f"Starting server on port {self.port}")
        
        self.logger.log(LogEvent.SERVER_START, f'Server started on port {self.port}, and under hostname {self.hostname}')

if __name__ == "__main__":
    # Check if number of command line parameters is correct
    num_args = len(sys.argv)
    if num_args < 2 or num_args > 3:
        print("Usage: python server.py [port] [?hostname]")
        sys.exit(1)

    # Convert port input parameter to integer
    try:
        port = int(sys.argv[1])
    except ValueError:
        print("Invalid port number. Port must be an integer.")
        sys.exit(1)

    # Assign hostname to default if no custom hostname was entered
    hostname = sys.argv[2] if num_args == 3 else DEFAULT_HOSTNAME

    # Create and start server
    server = Server(hostname, port)
    server.start()
