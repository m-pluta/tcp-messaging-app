# Python Messaging App

A basic console-based, client-server messaging application enabling real-time user communication & file sharing through a server using TCP sockets.

## Setup

**Run the server**: `python server.py [port]`

**Connect a client**: `python client.py [username] [hostname] [port]`


## Features

**Global (Broadcast) message**:
- Usage: `[message]`
- Params:
  - `message` - message to be sent

**Direct (Unicast) message**:
- Usage: `/msg [username] [message]`
- Params:
  - `username` - username of another connected user
  - `message` - message to be sent

**List available files**:
- Usage: `/list_files`

**File download**:
- Usage: `/download [filename]`
- Params:
  - `filename` - name of the file (including the file extension)

**Disconnect**:
- Usage: `/disconnect`

## Notes
- The codebase is PEP8 compliant.
  You can check compliance by running `pycodestyle src/.` in the terminal.

- The server can handle Keyboard Interrupts.

- The system enforces unique usernames.
  If a username is already taken, the user will be prompted to enter a new one. 

- The log file does not clear after each run.
  To change this, modify line 32 in server.py from
  `filemode='a'` to `filemode='w'`.
