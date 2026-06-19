# Import necessary libraries.
import discord

from src.dc.events import Events
from src.dc.groups import InterestGroups
from src.dc.scheduling import EventScheduler
from src.llm.client import create_client
from src.llm.conversation import Conversation
from src.llm.intent import wants_event
from src.storage.events import EventStore


class GLEM(discord.Client):
    def __init__(self):
        intents: discord.Intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)

        # Set up the AI client and the per-user conversation manager.
        self.conversation: Conversation = Conversation(create_client())
        # Manage game interest groups over the shared store.
        self.groups: InterestGroups = InterestGroups(self, self.conversation.store)
        # Schedule events and track RSVPs.
        self.events: Events = Events(
            self, self.conversation.store, EventStore()
        )
        # Guide users through event creation step by step.
        self.scheduler: EventScheduler = EventScheduler(
            self, self.conversation.store, self.events
        )

    async def on_ready(self):
        print(f"Logged in as {self.user}.")

    async def on_member_join(self, member: discord.Member):
        # Ignore other bots.
        if member.bot:
            return

        # Direct message the new member to ask about their games.
        greeting: str = self.conversation.greet(member.id)
        if greeting:
            channel: discord.DMChannel = await member.create_dm()
            await channel.send(greeting)

    async def on_message(self, message: discord.Message):
        # Ignore the bot's own messages.
        if message.author == self.user:
            return

        # Only respond to direct messages.
        if not isinstance(message.channel, discord.DMChannel):
            return

        user_id: int = message.author.id

        # If the user is mid-way through scheduling, continue that flow.
        if self.scheduler.is_active(user_id):
            await self.scheduler.handle_text(
                user_id, message.content, message.channel
            )
            return

        # Start the scheduling wizard if the user wants to create an event.
        if wants_event(self.conversation.client, message.content):
            await self.scheduler.start(user_id, message.channel)
            return

        # Track the user's games before and after this message.
        before: set[str] = self.conversation.current_games(user_id)

        # Generate and send the reply.
        async with message.channel.typing():
            reply: str = self.conversation.reply(user_id, message.content)
        if reply:
            # print(f"Replying to user {message.author.id}.")
            await message.channel.send(reply)

        # React to any games the user newly showed interest in.
        after: set[str] = self.conversation.current_games(user_id)
        for game in after - before:
            await self.groups.on_new_interest(user_id, game)


def create_bot() -> GLEM:
    return GLEM()