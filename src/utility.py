import re


def recv_to_buffer(socket, expected):
    total_data = b''
    received = 0
    while received != expected:
        print(received)
        read_size = min(expected - received, 65536)
        read_data = socket.recv(read_size)
        total_data += read_data
        received += len(read_data)

    return total_data

def recv_generator(socket, expected):
    received = 0
    while received != expected:
        print(received)
        read_size = min(expected - received, 65536)
        read_data = socket.recv(read_size)
        yield read_data
        received += len(read_data)


def extract_delimiter(input):
    # Using regular expression to extract data between <>
    match = re.search(r'<(.*?)>', input)

    if match:
        return match.group(1)
    return None
