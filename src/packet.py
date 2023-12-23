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

    def get(type: str):
        return PacketType(int(type))


@dataclass
class HeaderPacket():
    type: PacketType
    size: int

    def to_bytes(self, encoding=ENCODING):
        bytes = b''
        bytes += str(self.type.value).encode(encoding).ljust(4)
        bytes += str(self.size).encode(encoding).ljust(16)

        bytes = bytes.ljust(HEADER_SIZE)

        return bytes
    
    def decode(bytes, encoding=ENCODING):
        type = PacketType.get(bytes[:4].decode(encoding))
        bytes = bytes[4:]
        
        size = int(bytes[:16].decode(encoding))
        bytes = bytes[16:]
        return {'type': type, 'size': size}


@dataclass
class Packet:
    def to_bytes(self, encoding=ENCODING):
        packet_dict = asdict(self)

        content_bytes = b''

        for key, value in packet_dict.items():
            if key not in ('type', 'content'):
                if value is not None:
                    content_bytes += (f'<{value}>'.encode(encoding)
                                    .ljust(PACKET_SIZE))
                else:
                    content_bytes += (''.join([' '] * PACKET_SIZE)).encode(ENCODING)

        if 'content' in packet_dict:
            content_bytes += self.content.encode(encoding)

        header_packet = HeaderPacket(self.type, len(content_bytes))
        header_bytes = header_packet.to_bytes()

        return header_bytes + content_bytes
    

@dataclass
class MetadataPacket(Packet):
    content: str
    type: PacketType = PacketType.METADATA


@dataclass
class OutMessagePacket(Packet):
    content: str
    recipient: str
    type: PacketType = PacketType.OUT_MESSAGE


@dataclass
class InMessagePacket(Packet):
    content: str
    sender: str
    type: PacketType = PacketType.IN_MESSAGE


@dataclass
class AnnouncementPacket(Packet):
    content: str
    type: PacketType = PacketType.ANNOUNCEMENT


@dataclass
class FileListRequestPacket(Packet):
    type: PacketType = PacketType.FILE_LIST_REQUEST


@dataclass
class FileListPacket(Packet):
    type: PacketType = PacketType.FILE_LIST


@dataclass
class DownloadRequestPacket(Packet):
    content: str
    type: PacketType = PacketType.DOWNLOAD_REQUEST


@dataclass
class DownloadPacket(Packet):
    filename: str
    bytes: bytes
    type: PacketType = PacketType.DOWNLOAD

    def to_bytes(self, encoding=ENCODING):
        encoded_filename = f'<{self.filename}>'.encode(encoding)
        
        content_bytes = encoded_filename.ljust(PACKET_SIZE) + self.bytes

        header_packet = HeaderPacket(self.type, len(content_bytes))
        header_bytes = header_packet.to_bytes()

        return header_bytes + content_bytes


@dataclass
class DuplicateUsernamePacket(Packet):
    content: str
    type: PacketType = PacketType.DUPLICATE_USERNAME


if __name__ == "__main__":
    header_packet = HeaderPacket(PacketType.DOWNLOAD, 1761644)
    # print(header_packet.to_bytes())

    packet = MetadataPacket('user1')
    print(packet.to_bytes())
    packet = OutMessagePacket('Hey brian', 'brian')
    print(packet.to_bytes())
    packet = InMessagePacket('Hey Robbie', 'robbie')
    print(packet.to_bytes())
    packet = AnnouncementPacket('robbie has left the chat')
    print(packet.to_bytes())
    packet = FileListRequestPacket()
    print(packet.to_bytes())
    packet = DownloadRequestPacket('hi.txt')
    print(packet.to_bytes())
    packet = DuplicateUsernamePacket('robbie brian andy')
    print(packet.to_bytes())