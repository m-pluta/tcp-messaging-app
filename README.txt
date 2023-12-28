Program Usage Instructions


1. Disconnect:
    - Usage: '/disconnect'

2. Direct (Unicast) message:
    - Usage: '/msg [username] [message]'
    - Params:
      - username: username of another connected user
      - message: message to be sent

3. Global (Broadcast) message:
    - Usage: '[message]'
    - Params:
      - message: message to be sent

4. List available files:
    - Usage: '/list_files'

5. File download:
    - Usage: '/download [filename]'
    - Params:
      - filename: name of the file (including the file extension)


Notes:
- The codebase is PEP8 compliant.
  You can check compliance by running `pycodestyle src/.` in the terminal.

- The server can handle KeyboardInterrupts.

- The system enforces unique usernames.

- Active connections are stored in a list instead of a dictionary.
  This allows for handling duplicate usernames during connection.
  
- The log file does not clear after each run.
  To change this, modify line 32 in server.py from
  `filemode='a'` to `filemode='w'`.
