import sys
import threading
import time


def main():
    # Start a new thread to handle communication with the server
    server_thread = threading.Thread(target=handle_server_response)
    server_thread.daemon = True
    server_thread.start()

    handle_user_command()

def handle_server_response():
    while True:
        print('From server')
        time.sleep(2.5)


def handle_user_command():
    while True:
        try:
            user_input = str(input())
        except KeyboardInterrupt as e:
            print('Keyboard Interrupt')
            sys.exit(0)
            
        print(user_input.upper())

if __name__ == '__main__':
    main()
