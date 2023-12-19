from prompt_toolkit import prompt
import colorama
from colorama import Fore, Style

colorama.init()  # Initializes Colorama


def get_user_input():
    user_input = prompt("Enter your command: ",
                        # Add more features like auto-completion here
                        )
    return user_input


def main():
    while True:
        command = get_user_input()
        if command.lower() == 'exit':
            break
        print(Fore.GREEN + "You entered:" + Style.RESET_ALL, command)


if __name__ == "__main__":
    main()
