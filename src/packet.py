# Standard Library Imports
from dataclasses import dataclass, asdict
from enum import Enum

PACKET_SIZE = 1000           # Bytes
HEADER_SIZE = 100            # Bytes
ENCODING = 'utf-8'


class PacketType(Enum):
    METADATA = 1
    OUT_MESSAGE = 2
    IN_MESSAGE = 3
    ANNOUNCEMENT = 4
    FILE_LIST_REQUEST = 5
    FILE_LIST = 6
    DOWNLOAD_REQUEST = 7
    DOWNLOAD = 8
    DUPLICATE_USERNAME = 9


@dataclass
class HeaderPacket():
    type: PacketType
    size: int

    def to_bytes(self, ):
        bytes = b''
        bytes += str(self.type.value).encode(ENCODING).ljust(4)
        bytes += str(self.size).encode(ENCODING).ljust(16)

        return bytes.ljust(HEADER_SIZE)

    def decode(bytes: bytes):
        packet_type = PacketType(int(bytes[:4].decode(ENCODING)))
        bytes = bytes[4:]

        packet_size = int(bytes[:16].decode(ENCODING))
        bytes = bytes[16:]

        return {'type': packet_type, 'size': packet_size}


@dataclass
class Packet:
    content: str

    def to_bytes(self):
        packet_dict = asdict(self)

        bytes = b''

        for key, value in packet_dict.items():
            if key not in ('type', 'content'):
                if value is not None:
                    bytes += (f'<{value}>'.ljust(PACKET_SIZE).encode(ENCODING))
                else:
                    bytes += ((''.encode(ENCODING).ljust(PACKET_SIZE)))
                              

        if self.content:
            bytes += self.content.encode(ENCODING)

        header_packet = HeaderPacket(self.type, len(bytes))

        return header_packet.to_bytes() + bytes


@dataclass
class MetadataPacket(Packet):
    type: PacketType = PacketType.METADATA


@dataclass
class OutMessagePacket(Packet):
    recipient: str
    type: PacketType = PacketType.OUT_MESSAGE


@dataclass
class InMessagePacket(Packet):
    sender: str
    type: PacketType = PacketType.IN_MESSAGE


@dataclass
class AnnouncementPacket(Packet):
    type: PacketType = PacketType.ANNOUNCEMENT


@dataclass
class FileListRequestPacket(Packet):
    content: str = None
    type: PacketType = PacketType.FILE_LIST_REQUEST


@dataclass
class FileListPacket(Packet):
    type: PacketType = PacketType.FILE_LIST


@dataclass
class DownloadRequestPacket(Packet):
    type: PacketType = PacketType.DOWNLOAD_REQUEST


@dataclass
class DownloadPacket():
    filename: str
    bytes: bytes
    type: PacketType = PacketType.DOWNLOAD

    def to_bytes(self):
        encoded_filename = f'<{self.filename}>'.encode(ENCODING)

        bytes = encoded_filename.ljust(PACKET_SIZE) + self.bytes

        header_packet = HeaderPacket(self.type, len(bytes))

        return header_packet.to_bytes() + bytes


@dataclass
class DuplicateUsernamePacket(Packet):
    type: PacketType = PacketType.DUPLICATE_USERNAME
