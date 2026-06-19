# Import necessary libraries.
import json
import re

from openai import OpenAI
from openai.types.responses import Response

from src.config import MODEL, SYSTEM_PROMPT


def normalize_game(name: str) -> str:
    # Reduce a game name to lowercase alphanumerics for reliable matching.
    name = re.sub(r'[^a-z0-9 ]', '', name.lower())
    return re.sub(r'\s+', ' ', name).strip()

# Instructions for the extraction call that maintains the preferences list.
EXTRACT_PROMPT: str = (
    'You maintain a gamer\'s game preferences. '
    'You are given the user\'s existing preferences and their latest message. '
    'Each preference is an object mapping one game name to a skill level, '
    "where the level is one of 'beginner', 'intermediate', or 'expert'. "
    'If the message mentions games the user plays, or updates a known level, '
    'merge that into the list. Otherwise leave the list unchanged. '
    'Reply with ONLY a JSON array of these objects and nothing else, '
    'e.g. [{"Valorant": "beginner"}, {"CS2": "expert"}].'
)


def extract_preferences(client: OpenAI, user_inp: str,
                        current: list[dict]) -> list[dict]:
    # Ask the model to merge any game preferences in the message into the list.
    response: Response = client.responses.create(
        model=MODEL,
        instructions=EXTRACT_PROMPT,
        input=f'Existing preferences: {json.dumps(current)}\nMessage: {user_inp}',
        store=False,
        temperature=0.0,
    )

    # Parse the JSON reply, falling back to the current list on any failure.
    try:
        parsed = json.loads(response.output_text)
    except (json.JSONDecodeError, TypeError):
        return current
    if not isinstance(parsed, list):
        return current

    # Normalize every game name so common interests match reliably.
    return [
        {normalize_game(game): level for game, level in entry.items()}
        for entry in parsed
        if isinstance(entry, dict)
    ]


def build_instructions(preferences: list[dict], onboarded: bool,
                       server_context: str = '') -> str:
    # Once onboarded, just give the bot the user's known preferences.
    if onboarded:
        instructions: str = (
            f'{SYSTEM_PROMPT}\n\n'
            f'The user\'s known game preferences are: {json.dumps(preferences)}.'
        )
    else:
        # Until then, the bot should ask about the user's games.
        instructions = (
            f'{SYSTEM_PROMPT}\n\n'
            'You do not yet know which games this user plays. In your reply, '
            'naturally ask them which games they play and their skill level '
            '(beginner, intermediate, or expert).'
        )

    # Make the bot aware of server-wide interests and available channels.
    if server_context:
        instructions += f'\n\n{server_context}'
    return instructions
