# Import necessary libraries.
from openai import OpenAI
from openai.types.responses import Response

from src.config import API_KEY, MODEL, TEMPERATURE, MAX_TOKENS, SYSTEM_PROMPT


def create_client() -> OpenAI:
    # Initialise the OpenAI client.
    return OpenAI(api_key=API_KEY)


def get_response(client: OpenAI, user_inp: str,
                 previous_response_id: str | None,
                 instructions: str = SYSTEM_PROMPT) -> Response:
    # Continue the user's conversation chain, or start a new one.
    return client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=user_inp,
        previous_response_id=previous_response_id,
        store=True,
        temperature=TEMPERATURE,
        max_output_tokens=MAX_TOKENS,
    )
