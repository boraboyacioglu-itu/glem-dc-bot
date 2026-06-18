# Import necessary libraries.
import discord

from src.llm.client import create_client
from src.llm.conversation import Conversation


class GLEM(discord.Client):
    def __init__(self):
        intents: discord.Intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

        # Set up the AI client and the per-user conversation manager.
        self.conversation: Conversation = Conversation(create_client())

    async def on_ready(self):
        print(f'Logged in as {self.user}.')

    async def on_message(self, message: discord.Message):
        # Ignore the bot's own messages.
        if message.author == self.user:
            return

        # Only respond to direct messages.
        if not isinstance(message.channel, discord.DMChannel):
            return

        # Generate and send the reply.
        async with message.channel.typing():
            reply: str = self.conversation.reply(message.author.id, message.content)
        if reply:
            await message.channel.send(reply)


def create_bot() -> GLEM:
    return GLEM()