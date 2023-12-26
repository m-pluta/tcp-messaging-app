# Standard Library Imports
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