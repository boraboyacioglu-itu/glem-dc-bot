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

# Path to the JSON data file.
DATA_PATH: str = 'glem.json'

# Path to the JSON file holding scheduled events.
EVENTS_PATH: str = 'events.json'

# Timezone in which all event times are interpreted.
TIMEZONE: str = 'Europe/Berlin'

# Format users type event start times in.
DATETIME_FORMAT: str = '%Y-%m-%d %H:%M'

# Event duration options offered to the organizer, in hours.
EVENT_DURATIONS: list[int] = [1, 2, 3]

# System prompt.
SYSTEM_PROMPT: str = (
    'You are GLEM, a friendly gaming assistant on Discord. '
    'You chat with users in natural language through direct messages.'
)

# 
COMMON_USER_COUNT: int = 2