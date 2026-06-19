# Import necessary libraries.
import json
import os

from src.config import DATA_PATH


class Store:
    # Persists all bot data in a single JSON file.

    def __init__(self, path: str = DATA_PATH):
        self.path: str = path
        # Load existing data, or start with an empty structure.
        if os.path.exists(path):
            with open(path, 'r') as file:
                self.data: dict = json.load(file)
        else:
            self.data = {'conversations': {}, 'channels': {}}

    def _save(self) -> None:
        # Write the whole structure back to disk.
        with open(self.path, 'w') as file:
            json.dump(self.data, file, indent=2)

    def _user(self, user_id: int) -> dict:
        # Return the user's record, creating a default one if needed.
        return self.data['conversations'].setdefault(
            str(user_id),
            {
                'response_id': '',
                'preferences': [],
                'onboarded': False,
                'voice_channels': [],
            },
        )

    def get_response_id(self, user_id: int) -> str | None:
        # Return the user's latest response ID, or None if there is none yet.
        record: dict | None = self.data['conversations'].get(str(user_id))
        return record['response_id'] if record and record['response_id'] else None

    def set_response_id(self, user_id: int, response_id: str) -> None:
        # Insert or update the user's latest response ID.
        self._user(user_id)['response_id'] = response_id
        self._save()

    def get_preferences(self, user_id: int) -> list[dict]:
        # Return the user's game preferences as a list of {game: level} dicts.
        record: dict | None = self.data['conversations'].get(str(user_id))
        return record['preferences'] if record else []

    def set_preferences(self, user_id: int, preferences: list[dict]) -> None:
        # Insert or update the user's game preferences.
        self._user(user_id)['preferences'] = preferences
        self._save()

    def get_onboarded(self, user_id: int) -> bool:
        # Return whether the user has provided at least one interest.
        record: dict | None = self.data['conversations'].get(str(user_id))
        return bool(record['onboarded']) if record else False

    def set_onboarded(self, user_id: int, onboarded: bool) -> None:
        # Mark whether the user has been onboarded.
        self._user(user_id)['onboarded'] = int(onboarded)
        self._save()

    def get_voice_channels(self, user_id: int) -> list[str]:
        # Return the list of games whose channels the user has joined.
        record: dict | None = self.data['conversations'].get(str(user_id))
        return record['voice_channels'] if record else []

    def add_voice_channel(self, user_id: int, game: str) -> None:
        # Record that the user joined the given game's channel.
        channels: list[str] = self._user(user_id)['voice_channels']
        if game not in channels:
            channels.append(game)
            self._save()

    def users_in_channel(self, game: str) -> list[int]:
        # Return the IDs of all users who joined the game's voice channel.
        return [
            int(user_id)
            for user_id, record in self.data['conversations'].items()
            if game in record['voice_channels']
        ]

    def users_with_game(self, game: str) -> list[int]:
        # Return the IDs of all users whose preferences include the given game.
        return [
            int(user_id)
            for user_id, record in self.data['conversations'].items()
            if any(game in entry for entry in record['preferences'])
        ]

    def get_channel(self, game: str) -> int | None:
        # Return the channel ID created for the game, or None if there is none.
        return self.data['channels'].get(game)

    def set_channel(self, game: str, channel_id: int) -> None:
        # Record the channel created for a game.
        self.data['channels'][game] = channel_id
        self._save()

    def list_channels(self) -> list[str]:
        # Return the names of all games that have a channel.
        return list(self.data['channels'].keys())
