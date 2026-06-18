# Import necessary libraries.
from openai import OpenAI
from openai.types.responses import Response

from src.llm.client import get_response
from src.storage.store import Store


class Conversation:
    # Tracks each user's conversation.

    def __init__(self, client: OpenAI):
        self.client: OpenAI = client
        # Database storage mapping for previous response ID.
        self.store: Store = Store()

    def reply(self, user_id: int, user_inp: str) -> str:
        # Remember the user.
        prev_rid: str | None = self.store.get_response_id(user_id)

        response: Response = get_response(self.client, user_inp, prev_rid)
        self.store.set_response_id(user_id, response.id)

        return response.output_text
