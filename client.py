import sys

def connect(username, hostname, port):
    # Your client code goes here
    print(f"Connecting to server with username '{username}', hostname '{hostname}', and port {port}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python client.py [username] [hostname] [port]")
        sys.exit(1)

    username = sys.argv[1]
    hostname = sys.argv[2]

    try:
        port = int(sys.argv[3])
    except ValueError:
        print("Invalid port number. Port must be an integer.")
        sys.exit(1)

    connect(username, hostname, port)
