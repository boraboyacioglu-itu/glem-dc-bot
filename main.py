# Import necessary libraries.
import os
from dotenv import load_dotenv

from src.dc.bot import create_bot

# Load environment variables.
load_dotenv()
TOKEN: str = str(os.getenv('TOKEN'))


def main():
    # Create and run the chatbot.
    bot = create_bot()
    bot.run(TOKEN)


if __name__ == '__main__':
    main()