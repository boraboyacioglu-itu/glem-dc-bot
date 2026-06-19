# Import necessary libraries.
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord

from src.config import DATETIME_FORMAT, EVENT_DURATIONS, TIMEZONE
from src.dc.components import build_buttons
from src.dc.events import Events
from src.llm.preferences import normalize_game
from src.logger import logger
from src.storage.store import Store

# Units accepted in relative times, mapped to seconds.
RELATIVE_UNITS: dict[str, int] = {
    'minute': 60, 'minutes': 60, 'min': 60, 'mins': 60,
    'hour': 3600, 'hours': 3600, 'hr': 3600, 'hrs': 3600,
    'day': 86400, 'days': 86400,
}


def parse_when(text: str) -> datetime | None:
    # Parse an absolute ('2026-07-01 20:00') or relative ('in 2 hours') time.
    now: datetime = datetime.now(ZoneInfo(TIMEZONE))

    # Relative form: 'in <amount> <unit>', where the amount may be a/an.
    match = re.fullmatch(
        r'in\s+(\d+|a|an)\s+([a-z]+)', text.strip().lower()
    )
    if match:
        amount: int = 1 if match.group(1) in ('a', 'an') else int(match.group(1))
        unit: str | None = RELATIVE_UNITS.get(match.group(2))
        if unit is not None:
            return now + timedelta(seconds=amount * unit)

    # Absolute form in the configured timezone.
    try:
        return datetime.strptime(text.strip(), DATETIME_FORMAT).replace(
            tzinfo=ZoneInfo(TIMEZONE)
        )
    except ValueError:
        return None


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

    async def start(self, user_id: int, channel: discord.abc.Messageable,
                    details: dict) -> None:
        # Begin the wizard, pre-filling any details the user already gave.
        logger.info('Event wizard details for %s: %s', user_id, details)
        channels: list[str] = self.store.list_channels()
        if not channels:
            await channel.send(
                'There are no game channels yet, so I cannot schedule an event.'
            )
            return

        # Normalize the named game so it matches stored channel names.
        named = details.get('game')
        named = normalize_game(named) if named else None

        # Tell the user if they named a game that has no channel.
        if named and named not in channels:
            logger.info('No channel for "%s"; available: %s', named, channels)
            await channel.send(
                f'There is no channel for **{named}** yet, so I cannot '
                'schedule an event there. Pick an existing one instead.'
            )
            named = None

        self.drafts[user_id] = self._prefill({**details, 'game': named}, channels)
        await self._advance(user_id, channel)

    def _prefill(self, details: dict, channels: list[str]) -> dict:
        # Build a draft from the extracted details, keeping only valid values.
        draft: dict = {}

        game = details.get('game')
        if game and game in channels:
            draft['game'] = game
        if details.get('title'):
            draft['title'] = details['title']
        if details.get('when'):
            start: datetime | None = parse_when(details['when'])
            if start is not None and start > datetime.now(ZoneInfo(TIMEZONE)):
                draft['start'] = start
        duration = details.get('duration_hours')
        if isinstance(duration, int) and duration > 0:
            draft['duration'] = duration
        return draft

    async def _advance(self, user_id: int,
                       channel: discord.abc.Messageable) -> None:
        # Ask for the next missing detail, or create the event when complete.
        draft: dict = self.drafts[user_id]

        if 'game' not in draft:
            view: discord.ui.View = build_buttons(
                self.store.list_channels(), self._on_game(user_id)
            )
            await channel.send('Which game is the event for?', view=view)
        elif 'title' not in draft:
            draft['awaiting'] = 'title'
            await channel.send('What should the event be called?')
        elif 'start' not in draft:
            draft['awaiting'] = 'datetime'
            await channel.send(
                'When does it start? You can write a time like '
                f'`{DATETIME_FORMAT}` (e.g. 2026-07-01 20:00) in {TIMEZONE} time, '
                'or something relative like `in 2 hours`.'
            )
        elif 'duration' not in draft:
            labels: list[str] = [f'{hours}h' for hours in EVENT_DURATIONS]
            view = build_buttons(labels, self._on_duration(user_id))
            await channel.send('How long will it last?', view=view)
        else:
            await self._create(user_id, channel)

    def _on_game(self, user_id: int):
        # Button callback that records the chosen game.
        async def callback(interaction: discord.Interaction, label: str) -> None:
            self.drafts[user_id]['game'] = label
            await interaction.response.send_message(f'Game: **{label}**')
            await self._advance(user_id, interaction.channel)

        return callback

    async def handle_text(self, user_id: int, text: str,
                          channel: discord.abc.Messageable) -> None:
        # Fill the field the wizard is currently waiting on.
        draft: dict = self.drafts[user_id]
        awaiting: str | None = draft.pop('awaiting', None)

        if awaiting == 'title':
            draft['title'] = text
        elif awaiting == 'datetime':
            start: datetime | None = parse_when(text)
            if start is None:
                draft['awaiting'] = 'datetime'
                await channel.send('I could not read that time. Please try again.')
                return
            if start <= datetime.now(ZoneInfo(TIMEZONE)):
                draft['awaiting'] = 'datetime'
                await channel.send('That time is in the past. Please try again.')
                return
            draft['start'] = start
        else:
            return

        await self._advance(user_id, channel)

    def _on_duration(self, user_id: int):
        # Button callback that sets the duration and creates the event.
        async def callback(interaction: discord.Interaction, label: str) -> None:
            self.drafts[user_id]['duration'] = int(label.rstrip('h'))
            await interaction.response.send_message(f'Duration: **{label}**')
            await self._advance(user_id, interaction.channel)

        return callback

    async def _create(self, user_id: int,
                      channel: discord.abc.Messageable) -> None:
        # Create the event from a fully filled draft.
        draft: dict = self.drafts.pop(user_id)
        end: datetime = draft['start'] + timedelta(hours=draft['duration'])

        event = await self.events.schedule(
            draft['game'], draft['title'], draft['start'], end, user_id
        )
        if event is None:
            await channel.send('Something went wrong creating the event.')
            return

        # Creating an event makes the game an interest and joins the channel.
        game: str = draft['game']
        self.store.add_preference(user_id, game)
        self.store.add_voice_channel(user_id, game)
        await channel.send(
            f'Scheduled **{draft["title"]}** for {game}! '
            'I have invited everyone in the channel.'
        )
