# Import necessary libraries.
from datetime import datetime

import discord

from src.dc.components import build_buttons
from src.storage.events import EventStore
from src.storage.store import Store


async def create_event(guild: discord.Guild, name: str, start_time: datetime,
                       end_time: datetime, channel: discord.VoiceChannel,
                       description: str = ''
                       ) -> discord.ScheduledEvent:
    # Create a scheduled event to a voice channel.
    return await guild.create_scheduled_event(
        name=name,
        description=description,
        start_time=start_time,
        end_time=end_time,
        channel=channel,
        entity_type=discord.EntityType.voice,
        privacy_level=discord.PrivacyLevel.guild_only,
    )


class Events:
    # Schedules game events and tracks RSVPs from channel members.

    def __init__(self, client: discord.Client, store: Store,
                 event_store: EventStore):
        self.client: discord.Client = client
        self.store: Store = store
        self.event_store: EventStore = event_store

    async def schedule(self, game: str, name: str, start: datetime,
                       end: datetime, organizer_id: int
                       ) -> discord.ScheduledEvent | None:
        # Create a scheduled event for the game's channel and notify members.
        channel_id: int | None = self.store.get_channel(game)
        if channel_id is None:
            return None

        guild: discord.Guild = self.client.guilds[0]
        channel = guild.get_channel(channel_id)
        if not isinstance(channel, discord.VoiceChannel):
            return None

        event: discord.ScheduledEvent = await create_event(
            guild, name, start, end, channel, f'Game night for {game}!'
        )
        self.event_store.add_event(
            event.id, game, name, start, end, organizer_id
        )
        await self._notify(event, game, organizer_id)
        return event

    async def _notify(self, event: discord.ScheduledEvent, game: str,
                      organizer_id: int) -> None:
        # DM everyone who joined the game's channel an RSVP prompt.
        for user_id in self.store.users_in_channel(game):
            if user_id == organizer_id:
                continue
            user: discord.User | None = self.client.get_user(user_id)
            if user is None:
                continue

            view: discord.ui.View = build_buttons(['RSVP'], self._on_rsvp(event.id))
            await user.send(
                f'New **{game}** event scheduled: **{event.name}** '
                f'at {event.start_time}. Want to join?',
                view=view,
            )

    def _on_rsvp(self, event_id: int):
        # Build the RSVP button callback for a given event.
        async def callback(interaction: discord.Interaction, label: str) -> None:
            self.event_store.add_rsvp(event_id, interaction.user.id)
            await interaction.response.send_message(
                'You are on the list! See you there.', ephemeral=True
            )

        return callback
