# Import necessary libraries.
import sqlite3

from src.config import DB_PATH


class Store:

    def __init__(self, path: str = DB_PATH):
        # Open the connection and ensure the schema exists.
        self.conn: sqlite3.Connection = sqlite3.connect(path)
        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS conversations ('
            'user_id INTEGER PRIMARY KEY, '
            'response_id TEXT NOT NULL)'
        )
        self.conn.commit()

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
