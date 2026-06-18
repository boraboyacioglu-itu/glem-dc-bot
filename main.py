# Import necessary libraries.
from src.config import TOKEN
from src.dc.bot import create_bot


def main():
    # Create and run the chatbot.
    bot = create_bot()
    bot.run(TOKEN)


if __name__ == '__main__':
    main()