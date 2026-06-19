# Import necessary libraries.
from openai import OpenAI
from openai.types.responses import Response

from src.config import MODEL

# Instructions for the intent classifier.
INTENT_PROMPT: str = (
    'Decide whether the user wants to schedule or create a gaming event. '
    "Reply with only the single word 'yes' or 'no'."
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
