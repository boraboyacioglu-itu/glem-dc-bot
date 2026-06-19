# Import necessary libraries.
import logging

from src.config import LOG_PATH

# Configure logging to both the log file and the console.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8'),
        logging.StreamHandler(),
    ],
)

# Quiet noisy third-party loggers so the log stays focused on the bot.
for noisy in ('httpx', 'openai', 'discord'):
    logging.getLogger(noisy).setLevel(logging.WARNING)

# Shared logger for the whole bot.
logger: logging.Logger = logging.getLogger('glem')
