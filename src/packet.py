# Standard Library Imports
from dataclasses import dataclass, asdict
import json
from enum import Enum

HEADER_SIZE = 128  # Bytes


class PacketType(Enum):
    HEADER = 1
    METADATA = 2
    OUT_MESSAGE = 3
    IN_MESSAGE = 4
    ANNOUNCEMENT = 5
    FILE_LIST_REQUEST = 6
    DOWNLOAD_REQUEST = 7


@dataclass
class Packet:
    def to_json(self):
        return json.dumps(self.get_serialisable_dict())

    def get_serialisable_dict(self):
        packet_dict = asdict(self)

        # Convert PacketType enum to its name for JSON serialization
        if 'type' in packet_dict:
            packet_dict['type'] = packet_dict['type'].value

        return packet_dict

    def loads(data):
        return json.loads(data)


def send_packet(socket, packet: Packet):
    encoded_packet = packet.to_json().encode()

    header_packet = HeaderPacket(len(encoded_packet))

    print(encoded_packet)
    print(header_packet)

    socket.send(header_packet.to_json().encode())
    socket.send(encoded_packet)


@dataclass
class HeaderPacket(Packet):
    size: int
    type: PacketType = PacketType.HEADER

    def to_json(self):
        header_json = json.dumps(self.get_serialisable_dict())

        padded_json = header_json.ljust(HEADER_SIZE)

        return padded_json


@dataclass
class MetadataPacket(Packet):
    username: str
    type: PacketType = PacketType.METADATA


@dataclass
class MessagePacketBase(Packet):
    content: str


@dataclass
class OutMessagePacket(MessagePacketBase):
    recipient: str
    type: PacketType = PacketType.OUT_MESSAGE


@dataclass
class InMessagePacket(MessagePacketBase):
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
class DownloadRequestPacket(Packet):
    filename: str
    type: PacketType = PacketType.DOWNLOAD_REQUEST
