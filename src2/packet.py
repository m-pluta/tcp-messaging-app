from packet_type import PacketType

HEADER_SIZE = 1024
delimiter = '<###>'

def encode_header(packet_type: PacketType, packet_size: int, **kwargs: dict):
    header_bytes = b''
    header_bytes += str(packet_type.value).encode().ljust(2)
    header_bytes += str(packet_size).encode().ljust(16)

    for kwarg, value in kwargs.items():
        text = f'{kwarg}:{str(value)}{delimiter}'
        header_bytes += text.encode()

    return header_bytes.ljust(HEADER_SIZE)


def decode_header(data: bytes):
    packet_type = PacketType(int(data[0:2].decode()))
    packet_size = int(data[2:18].decode())

    encoded_values = data[18:].decode().rstrip().split(delimiter)[:-1]
    decoded_values = {}

    for value in encoded_values:
        key, val = value.split(':')
        decoded_values[key] = val

    return packet_type, packet_size, decoded_values
