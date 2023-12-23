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

def recv_generator(socket, expected, chunk_size=65536):
    received = 0
    while received < expected:
        read_size = min(expected - received, chunk_size)
        read_data = socket.recv(read_size)
        if not read_data:
            break
        received += len(read_data)
        yield read_data

def extract_delimiter(text):
    match = re.search(r'<(.*?)>', text)
    return match.group(1) if match else None
