# Import necessary libraries.
import discord

from src.config import COMMON_USER_COUNT
from src.dc.components import build_buttons
from src.storage.store import Store


class InterestGroups:
    # Forms voice channels around games that enough users share.

    def __init__(self, client: discord.Client, store: Store):
        self.client: discord.Client = client
        self.store: Store = store
        # Games for which a creation poll has been sent but no channel exists yet.
        self.pending: set[str] = set()

    async def on_new_interest(self, user_id: int, game: str) -> None:
        # React to a user newly showing interest in a game.
        channel_id: int | None = self.store.get_channel(game)

        # A channel already exists: suggest the user join it.
        if channel_id is not None:
            await self._suggest_join(user_id, game, channel_id)
            return

        # Enough users share the game and no poll is pending: propose a channel.
        members: list[int] = self.store.users_with_game(game)
        if len(members) >= COMMON_USER_COUNT and game not in self.pending:
            self.pending.add(game)
            await self._send_creation_poll(game, members)

    async def _send_creation_poll(self, game: str, members: list[int]) -> None:
        # DM every interested user a yes/no prompt to create the channel.
        for user_id in members:
            user: discord.User | None = self.client.get_user(user_id)
            if user is None:
                continue

            view: discord.ui.View = build_buttons(
                ['Yes', 'No'], self._on_vote(game)
            )
            await user.send(
                f'Several players are interested in **{game}**. '
                'Should I create a voice channel for it?',
                view=view,
            )

    def _on_vote(self, game: str):
        # Build the button callback for a given game's creation poll.
        async def callback(interaction: discord.Interaction, label: str) -> None:
            if label == 'Yes':
                await self._create_or_join(interaction.user.id, game)
                await interaction.response.send_message(
                    f'Done! You are in the **{game}** channel.', ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    'No problem, maybe next time!', ephemeral=True
                )

        return callback

    async def _create_or_join(self, user_id: int, game: str) -> None:
        # Create the game's channel if needed, then grant the user access.
        channel_id: int | None = self.store.get_channel(game)
        if channel_id is None:
            guild: discord.Guild = self.client.guilds[0]
            channel: discord.VoiceChannel = await guild.create_voice_channel(game)
            self.store.set_channel(game, channel.id)
            self.pending.discard(game)
            channel_id = channel.id

        await self._grant_access(user_id, channel_id)

    async def _grant_access(self, user_id: int, channel_id: int) -> None:
        # Allow the user into the channel and send them a jump link.
        guild: discord.Guild = self.client.guilds[0]
        channel = guild.get_channel(channel_id)
        member: discord.Member | None = guild.get_member(user_id)
        if channel is None or member is None:
            return

        await channel.set_permissions(member, view_channel=True, connect=True)
        user: discord.User | None = self.client.get_user(user_id)
        if user is not None:
            await user.send(f'Jump into the channel here: {channel.jump_url}')

    async def _suggest_join(self, user_id: int, game: str, channel_id: int) -> None:
        # Suggest an existing channel to a user who just showed the interest.
        user: discord.User | None = self.client.get_user(user_id)
        if user is None:
            return

        view: discord.ui.View = build_buttons(['Join'], self._on_join(game))
        await user.send(
            f'There is already a voice channel for **{game}**. '
            'Want me to add you?',
            view=view,
        )

    def _on_join(self, game: str):
        # Build the button callback for joining an existing channel.
        async def callback(interaction: discord.Interaction, label: str) -> None:
            await self._create_or_join(interaction.user.id, game)
            await interaction.response.send_message(
                f'Added you to the **{game}** channel!', ephemeral=True
            )

        return callback
