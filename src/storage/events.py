# Import necessary libraries.
import json
import os
from datetime import datetime

from src.config import EVENTS_PATH


class EventStore:
    # Persists scheduled events and their RSVPs in a JSON file.

    def __init__(self, path: str = EVENTS_PATH):
        self.path: str = path
        # Load existing events, or start with an empty structure.
        if os.path.exists(path):
            with open(path, 'r') as file:
                self.data: dict = json.load(file)
        else:
            self.data = {'events': {}}

    def _save(self) -> None:
        # Write the whole structure back to disk.
        with open(self.path, 'w') as file:
            json.dump(self.data, file, indent=2)

    def add_event(self, event_id: int, game: str, name: str,
                  start: datetime, end: datetime, organizer_id: int) -> None:
        # Record a newly scheduled event.
        self.data['events'][str(event_id)] = {
            'game': game,
            'name': name,
            'start': start.isoformat(),
            'end': end.isoformat(),
            'organizer_id': organizer_id,
            'rsvps': [organizer_id],
        }
        self._save()

    def add_rsvp(self, event_id: int, user_id: int) -> None:
        # Record a user's RSVP to an event.
        event: dict | None = self.data['events'].get(str(event_id))
        if event is None or user_id in event['rsvps']:
            return
        event['rsvps'].append(user_id)
        self._save()

    def get_event(self, event_id: int) -> dict | None:
        # Return a single event, or None if it does not exist.
        return self.data['events'].get(str(event_id))
