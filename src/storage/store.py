# Import necessary libraries.
import json
import sqlite3

from src.config import DB_PATH


class Store:

    def __init__(self, path: str = DB_PATH):
        # Open the connection and ensure the schema exists.
        self.conn: sqlite3.Connection = sqlite3.connect(path)
        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS conversations ('
            'user_id INTEGER PRIMARY KEY, '
            'response_id TEXT NOT NULL, '
            "preferences TEXT NOT NULL DEFAULT '[]')"
        )
        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS channels ('
            'game TEXT PRIMARY KEY, '
            'channel_id INTEGER NOT NULL)'
        )
        self._migrate()
        self.conn.commit()

    def _migrate(self) -> None:
        # Add the preferences column to databases created before it existed.
        names: set = {
            column[1]
            for column in self.conn.execute('PRAGMA table_info(conversations)')
        }
        if 'preferences' not in names:
            self.conn.execute(
                "ALTER TABLE conversations "
                "ADD COLUMN preferences TEXT NOT NULL DEFAULT '[]'"
            )

    def get_response_id(self, user_id: int) -> str | None:
        # Return the user's latest response ID,
        # or None if they are new.
        row: tuple | None = self.conn.execute(
            'SELECT response_id FROM conversations WHERE user_id = ?',
            (user_id,),
        ).fetchone()
        return row[0] if row else None

    def set_response_id(self, user_id: int, response_id: str) -> None:
        # Insert or update the user's latest response ID.
        self.conn.execute(
            'INSERT INTO conversations (user_id, response_id) VALUES (?, ?) '
            'ON CONFLICT(user_id) DO UPDATE SET response_id = excluded.response_id',
            (user_id, response_id),
        )
        self.conn.commit()

    def get_preferences(self, user_id: int) -> list[dict]:
        # Return the user's game preferences as a list of {game: level} dicts.
        row: tuple | None = self.conn.execute(
            'SELECT preferences FROM conversations WHERE user_id = ?',
            (user_id,),
        ).fetchone()
        return json.loads(row[0]) if row else []

    def set_preferences(self, user_id: int, preferences: list[dict]) -> None:
        # Insert or update the user's game preferences.
        encoded: str = json.dumps(preferences)
        self.conn.execute(
            'INSERT INTO conversations (user_id, response_id, preferences) '
            "VALUES (?, '', ?) "
            'ON CONFLICT(user_id) DO UPDATE SET preferences = excluded.preferences',
            (user_id, encoded),
        )
        self.conn.commit()

    def users_with_game(self, game: str) -> list[int]:
        # Return the IDs of all users whose preferences include the given game.
        rows: list = self.conn.execute(
            'SELECT user_id, preferences FROM conversations'
        ).fetchall()
        return [
            user_id
            for user_id, preferences in rows
            if any(game in entry for entry in json.loads(preferences))
        ]

    def get_channel(self, game: str) -> int | None:
        # Return the channel ID created for the game, or None if there is none.
        row: tuple | None = self.conn.execute(
            'SELECT channel_id FROM channels WHERE game = ?',
            (game,),
        ).fetchone()
        return row[0] if row else None

    def set_channel(self, game: str, channel_id: int) -> None:
        # Record the channel created for a game.
        self.conn.execute(
            'INSERT INTO channels (game, channel_id) VALUES (?, ?) '
            'ON CONFLICT(game) DO UPDATE SET channel_id = excluded.channel_id',
            (game, channel_id),
        )
        self.conn.commit()
