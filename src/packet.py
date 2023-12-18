# Standard Library Imports
from dataclasses import dataclass, asdict
import json
from enum import Enum
import uuid


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
            packet_dict['type'] = packet_dict['type'].name

        # Convert UUID to string for JSON serialization
        if 'tran_id' in packet_dict:
            packet_dict['tran_id'] = str(packet_dict['tran_id'])

        return packet_dict


@dataclass
class NetworkPacket(Packet):
    tran_id: uuid.UUID
    frag_id: int
    data: dict


@dataclass
class HeaderPacket(Packet):
    size: int
    type: PacketType = PacketType.HEADER


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


if __name__ == "__main__":
    packet = OutMessagePacket(content="Hi Alice", recipient="Alice")
    print(packet)
    print(packet.to_json())

    tran_id = uuid.uuid4()
    network_packet = NetworkPacket(tran_id=tran_id, frag_id=0, data=packet.get_serialisable_dict())
    print(network_packet)
    print(network_packet.to_json())
