# Standard Library Imports
from enum import Enum


class PacketType(Enum):
    USERNAME = 1
    OUT_MESSAGE = 2
    IN_MESSAGE = 3
    ANNOUNCEMENT = 4
    FILE_LIST_REQUEST = 5
    FILE_LIST = 6
    DUPLICATE_USERNAME = 7
    DOWNLOAD_REQUEST = 8
    DOWNLOAD = 9
