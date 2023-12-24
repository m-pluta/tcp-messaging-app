import re


# Reads the expected number of bytes from the socket in chunks.
# Returns the bytes in one go.
def recv_full(socket, expected, chunk_size=65536):
    total_data = b''
    received = 0
    while received < expected:
        read_size = min(expected - received, chunk_size)
        read_data = socket.recv(read_size)
        if not read_data:
            break
        total_data += read_data
        received += len(read_data)

    return total_data


# Reads the expected number of bytes from the socket in chunks.
# Returns the bytes as a generator.
# This means during download, server doesn't load the entire file into memory.
def recv_generator(socket, expected, chunk_size=65536):
    received = 0
    while received < expected:
        read_size = min(expected - received, chunk_size)
        read_data = socket.recv(read_size)
        if not read_data:
            break
        received += len(read_data)
        yield read_data


# Extracts packet parameters stored between delimiters.
def extract_from_delimiter(text):
    match = re.search(r'<(.*?)>', text)
    return match.group(1) if match else None
