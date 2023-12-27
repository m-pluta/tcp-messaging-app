# Standard Library Imports
from enum import Enum, auto


class PacketType(Enum):
    USERNAME = auto()
    OUT_MESSAGE = auto()
    IN_MESSAGE = auto()
    ANNOUNCEMENT = auto()
    FILE_LIST_REQUEST = auto()
    FILE_LIST = auto()
    DUPLICATE_USERNAME = auto()
    DOWNLOAD_REQUEST = auto()
    DOWNLOAD = auto()
