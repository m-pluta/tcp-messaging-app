from socket import socket
from packet_type import PacketType

HEADER_SIZE = 1024
DELIMITER = '<###>'


def encode_header(packet_type: PacketType, packet_size: int, **kwargs: dict):
    header_bytes = b''
    header_bytes += str(packet_type.value).encode().ljust(2)
    header_bytes += str(packet_size).encode().ljust(16)

    for kwarg, value in kwargs.items():
        header_bytes += f'{kwarg}:{str(value)}{DELIMITER}'.encode()

    return header_bytes.ljust(HEADER_SIZE)


def decode_header(data: bytes):
    packet_type = PacketType(int(data[:2].decode()))
    packet_size = int(data[2:18].decode())

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
        read_data = socket.recv(min(chunk_size, expected - received))
        if not read_data:
            break
        received += len(read_data)
        yield read_data
