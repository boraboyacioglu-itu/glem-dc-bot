# Import necessary libraries.
from openai import OpenAI
from openai.types.responses import Response

from src.llm.client import get_response
from src.llm.preferences import extract_preferences, build_instructions
from src.storage.store import Store


class Conversation:
    # Tracks each user's conversation.

    def __init__(self, client: OpenAI):
        self.client: OpenAI = client
        # Database storage mapping for previous response ID.
        self.store: Store = Store()

    def _update_preferences(self, user_id: int, user_inp: str) -> list[dict]:
        # Extract any game preferences from the message and persist changes.
        current: list[dict] = self.store.get_preferences(user_id)
        updated: list[dict] = extract_preferences(self.client, user_inp, current)
        if updated != current:
            self.store.set_preferences(user_id, updated)
        return updated

    def reply(self, user_id: int, user_inp: str) -> str:
        # Keep preferences current, then answer with them in context.
        preferences: list[dict] = self._update_preferences(user_id, user_inp)
        instructions: str = build_instructions(preferences)

        prev_rid: str | None = self.store.get_response_id(user_id)
        response: Response = get_response(
            self.client, user_inp, prev_rid, instructions
        )
        self.store.set_response_id(user_id, response.id)

        return response.output_text

    def greet(self, user_id: int) -> str:
        # Open a conversation with a new user, asking about their games.
        instructions: str = build_instructions(self.store.get_preferences(user_id))

        prev_rid: str | None = self.store.get_response_id(user_id)
        response: Response = get_response(
            self.client,
            'A new user just joined the server. Greet them warmly.',
            prev_rid,
            instructions,
        )
        self.store.set_response_id(user_id, response.id)

        return response.output_text
