# Import necessary libraries.
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion

from src.config import API_KEY, MODEL, TEMPERATURE, MAX_TOKENS


def create_client() -> OpenAI:
    # Initialise the OpenAI client.
    return OpenAI(api_key=API_KEY)


def get_response(client: OpenAI, messages: list) -> str:
    # Get the response.
    response: ChatCompletion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )

    # Return the reply text, or an empty string if there is none.
    reply: str = str(response.choices[0].message.content)
    return reply if reply else ''