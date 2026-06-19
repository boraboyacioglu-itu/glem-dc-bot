# Import necessary libraries.
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord

from src.config import DATETIME_FORMAT, EVENT_DURATIONS, TIMEZONE
from src.dc.components import build_buttons
from src.dc.events import Events
from src.storage.store import Store


class EventScheduler:
    # Guides a user through creating an event one step at a time.

    def __init__(self, client: discord.Client, store: Store, events: Events):
        self.client: discord.Client = client
        self.store: Store = store
        self.events: Events = events
        # In-progress event drafts, keyed by user ID.
        self.drafts: dict[int, dict] = {}

    def is_active(self, user_id: int) -> bool:
        # Whether the user is currently building an event.
        return user_id in self.drafts

    async def start(self, user_id: int, channel: discord.abc.Messageable) -> None:
        # Begin the wizard by asking which game the event is for.
        games: list[str] = self.store.list_channels()
        if not games:
            await channel.send(
                'There are no game channels yet, so I cannot schedule an event.'
            )
            return

        self.drafts[user_id] = {'step': 'game'}
        view: discord.ui.View = build_buttons(games, self._on_game(user_id))
        await channel.send('Which game is the event for?', view=view)

    def _on_game(self, user_id: int):
        # Button callback that records the chosen game.
        async def callback(interaction: discord.Interaction, label: str) -> None:
            self.drafts[user_id]['game'] = label
            self.drafts[user_id]['step'] = 'title'
            await interaction.response.send_message(
                'Great! What should the event be called?'
            )

        return callback

    async def handle_text(self, user_id: int, text: str,
                          channel: discord.abc.Messageable) -> None:
        # Advance the wizard based on the user's typed input.
        draft: dict = self.drafts[user_id]

        if draft['step'] == 'title':
            draft['title'] = text
            draft['step'] = 'datetime'
            await channel.send(
                'When does it start? Use the format '
                f'`{DATETIME_FORMAT}` (e.g. 2026-07-01 20:00), '
                f'in {TIMEZONE} time.'
            )

        elif draft['step'] == 'datetime':
            try:
                start: datetime = datetime.strptime(text, DATETIME_FORMAT)
            except ValueError:
                await channel.send('I could not read that. Please try again.')
                return
            draft['start'] = start.replace(tzinfo=ZoneInfo(TIMEZONE))
            draft['step'] = 'duration'
            labels: list[str] = [f'{hours}h' for hours in EVENT_DURATIONS]
            view: discord.ui.View = build_buttons(labels, self._on_duration(user_id))
            await channel.send('How long will it last?', view=view)

    def _on_duration(self, user_id: int):
        # Button callback that sets the duration and creates the event.
        async def callback(interaction: discord.Interaction, label: str) -> None:
            draft: dict = self.drafts.pop(user_id)
            hours: int = int(label.rstrip('h'))
            end: datetime = draft['start'] + timedelta(hours=hours)

            event = await self.events.schedule(
                draft['game'], draft['title'], draft['start'], end, user_id
            )
            if event is None:
                await interaction.response.send_message(
                    'Something went wrong creating the event.'
                )
            else:
                await interaction.response.send_message(
                    f'Scheduled **{draft["title"]}** for {draft["game"]}! '
                    'I have invited everyone in the channel.'
                )

        return callback
