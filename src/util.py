# Local Imports
from socket import socket
from packet_type import PacketType

HEADER_SIZE = 1024
DELIMITER = '<###>'


def encode_header(packet_type: PacketType, packet_size: int, **kwargs: dict):
    # First 2 bytes: packet type
    # Next 16 bytes: packet size
    header_bytes = f"{packet_type.value:02d}{packet_size:016d}".encode()

    # Remaining kwargs are added to header seperated by DELIMITER
    for kwarg, value in kwargs.items():
        header_bytes += f'{kwarg}:{str(value)}{DELIMITER}'.encode()

    # Header size is fixed to HEADER_SIZE number of bytes
    return header_bytes.ljust(HEADER_SIZE)


def decode_header(data: bytes):
    # Extract the packet type & size
    packet_type = PacketType(int(data[:2].decode()))
    packet_size = int(data[2:18].decode())

    # Extract additional key-value pairs from the header
    encoded_values = data[18:].decode().rstrip().split(DELIMITER)[:-1]
    decoded_values = {}
    for value in encoded_values:
        key, val = value.split(':')
        decoded_values[key] = val

    return packet_type, packet_size, decoded_values


# Reads the expected number of bytes from the socket in chunks.
# Returns the bytes as a generator.
# This means during download, the entire file isn't loaded into memory.
def recv_generator(socket: socket, expected: int, chunk_size=65536):
    received = 0
    while received < expected:
        # Receive data in chunks and yield each chunk
        data = socket.recv(min(chunk_size, expected - received))
        if not data:
            break
        received += len(data)
        yield data
