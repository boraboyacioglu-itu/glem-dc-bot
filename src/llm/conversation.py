# Import necessary libraries.
from openai import OpenAI

from src.config import HISTORY_LIMIT, SYSTEM_PROMPT
from src.llm.client import get_response


class Conversation:
    # Holds the in-memory chat context for the active users.

    def __init__(self, client: OpenAI):
        self.client: OpenAI = client
        # Map each user ID to their recent message history.
        self.histories: dict[int, list] = {}

    def _history(self, user_id: int) -> list:
        # Return the user's history, creating it with the system prompt if new.
        if user_id not in self.histories:
            self.histories[user_id] = [
                {'role': 'system', 'content': SYSTEM_PROMPT}
            ]
        return self.histories[user_id]

    def _trim(self, history: list) -> None:
        # Keep the system prompt plus the most recent messages only.
        if len(history) > HISTORY_LIMIT + 1:
            del history[1:-HISTORY_LIMIT]

    def reply(self, user_id: int, user_inp: str) -> str:
        # Append the user message, query the model, and store the reply.
        history: list = self._history(user_id)
        history.append({'role': 'user', 'content': user_inp})

        reply: str = get_response(self.client, history)
        if reply:
            history.append({'role': 'assistant', 'content': reply})

        self._trim(history)
        return reply
