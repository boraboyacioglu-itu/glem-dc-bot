# Import necessary libraries.
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from openai import OpenAI
from openai.types.responses import Response

from src.config import DATETIME_FORMAT, MODEL, TIMEZONE

# Instructions for the intent classifier.
INTENT_PROMPT: str = (
    'Decide whether the user wants to schedule or create a gaming event. '
    "Reply with only the single word 'yes' or 'no'."
)

# Instructions for extracting event details from a message.
DETAILS_PROMPT: str = (
    'Extract event details from the user\'s message. Reply with ONLY a JSON '
    'object with the keys "game", "title", "when", and "duration_hours". '
    'Use null for anything the user did not mention. '
    '"game" is a short lowercase game name. '
    f'"when" must be an absolute time formatted as "{DATETIME_FORMAT}", '
    'computed from the given current time if the user spoke relatively '
    '(e.g. "in two hours"); otherwise null. '
    '"duration_hours" is an integer number of hours, or null.'
)


def wants_event(client: OpenAI, user_inp: str) -> bool:
    # Classify whether the message is a request to schedule an event.
    response: Response = client.responses.create(
        model=MODEL,
        instructions=INTENT_PROMPT,
        input=user_inp,
        store=False,
        temperature=0.0,
    )
    return response.output_text.strip().lower().startswith('yes')


def extract_event_details(client: OpenAI, user_inp: str) -> dict:
    # Pull any event details the user already provided from their message.
    now: str = datetime.now(ZoneInfo(TIMEZONE)).strftime(DATETIME_FORMAT)
    response: Response = client.responses.create(
        model=MODEL,
        instructions=DETAILS_PROMPT,
        input=f'Current time: {now}\nMessage: {user_inp}',
        store=False,
        temperature=0.0,
    )
    try:
        parsed = json.loads(response.output_text)
        return parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}
