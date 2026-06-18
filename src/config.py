# Import necessary libraries.
import os
from dotenv import load_dotenv

# Load environment variables.
load_dotenv()

TOKEN: str = str(os.getenv('TOKEN'))
API_KEY: str = str(os.getenv('OPENAI_API_KEY'))

# Model configuration.
MODEL: str = 'gpt-4.1-nano'
TEMPERATURE: float = 0.7
MAX_TOKENS: int = 256

# System prompt.
SYSTEM_PROMPT: str = (
    'You are GLEM, a friendly gaming assistant on Discord. '
    'You chat with users in natural language through direct messages.'
)

# Num. of most recent messages to keep per user.
HISTORY_LIMIT: int = 10