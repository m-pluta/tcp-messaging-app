# Standard Library Imports
from dataclasses import dataclass, asdict
import json


@dataclass
class Packet:
    def to_json(self):
        return json.dumps(asdict(self))

    def loads(data):
        return json.loads(data)


@dataclass
class MetadataPacket(Packet):
    username: str
    type: str = "metadata"


@dataclass
class MessagePacket(Packet):
    sender: str
    recipient: str
    content: str
    type: str = "message"


@dataclass
class FileListRequestPacket(Packet):
    type: str = "file_list_request"


@dataclass
class FileRequestPacket(Packet):
    filename: str
    type: str = "file_request"


def parse_packet(packet_string):
    return json.loads(packet_string)
