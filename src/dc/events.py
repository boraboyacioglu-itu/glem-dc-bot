# Import necessary libraries.
from datetime import datetime

import discord

from src.logger import logger
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


class RSVPTracker(discord.ui.View):
    # A live message showing event details and everyone who has joined.

    def __init__(self, client: discord.Client, event_store: EventStore,
                 event_id: int):
        super().__init__(timeout=None)
        self.client: discord.Client = client
        self.event_store: EventStore = event_store
        self.event_id: int = event_id

    def build_embed(self) -> discord.Embed:
        # Build the tracking embed from the stored event and its RSVPs.
        event: dict = self.event_store.get_event(self.event_id) or {}
        embed: discord.Embed = discord.Embed(
            title=event.get('name', 'Event'),
            description=f'Game: **{event.get("game", "?")}**',
            colour=discord.Colour.blurple(),
        )
        embed.add_field(name='Starts', value=event.get('start', '?'), inline=True)
        embed.add_field(name='Ends', value=event.get('end', '?'), inline=True)

        names: list[str] = []
        for user_id in event.get('rsvps', []):
            user: discord.User | None = self.client.get_user(user_id)
            names.append(user.display_name if user else f'<@{user_id}>')
        embed.add_field(
            name=f'Joined ({len(names)})',
            value='\n'.join(names) if names else 'Nobody yet',
            inline=False,
        )
        return embed

    @discord.ui.button(label='RSVP', style=discord.ButtonStyle.success)
    async def rsvp(self, interaction: discord.Interaction,
                   button: discord.ui.Button) -> None:
        # Record the RSVP and refresh the tracker for everyone.
        self.event_store.add_rsvp(self.event_id, interaction.user.id)
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


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
            logger.error('Cannot schedule %s: no channel recorded.', game)
            return None

        guild: discord.Guild = self.client.guilds[0]
        channel = guild.get_channel(channel_id)
        if not isinstance(channel, discord.VoiceChannel):
            logger.error(
                'Cannot schedule %s: channel %s missing or not a voice channel.',
                game, channel_id,
            )
            return None

        try:
            event: discord.ScheduledEvent = await create_event(
                guild, name, start, end, channel, f'Game night for {game}!'
            )
        except discord.HTTPException as error:
            logger.exception('Failed to create event "%s": %s', name, error)
            return None

        self.event_store.add_event(
            event.id, game, name, start, end, organizer_id
        )
        logger.info(
            'Created event "%s" for %s at %s (organizer %s).',
            name, game, start.isoformat(), organizer_id,
        )

        # Post the live tracking UI in the channel.
        tracker: RSVPTracker = RSVPTracker(self.client, self.event_store, event.id)
        message: discord.Message = await channel.send(
            embed=tracker.build_embed(), view=tracker
        )
        await self._notify(game, organizer_id, message.jump_url)
        return event

    async def _notify(self, game: str, organizer_id: int, link: str) -> None:
        # DM everyone who joined the game's channel a link to the tracker.
        for user_id in self.store.users_in_channel(game):
            if user_id == organizer_id:
                continue
            user: discord.User | None = self.client.get_user(user_id)
            if user is None:
                continue
            await user.send(
                f'A new **{game}** event was scheduled! RSVP here: {link}'
            )
