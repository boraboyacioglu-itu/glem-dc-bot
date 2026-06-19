# Import necessary libraries.
import discord

from src.dc.events import Events
from src.dc.groups import InterestGroups
from src.dc.scheduling import EventScheduler
from src.llm.client import create_client
from src.llm.conversation import Conversation
from src.llm.intent import extract_event_details, wants_event
from src.logger import logger
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
        logger.info('Logged in as %s.', self.user)

    async def on_error(self, event_method: str, *args, **kwargs):
        # Log any uncaught error raised inside an event handler.
        logger.exception('Unhandled error in %s.', event_method)

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
        logger.info('DM from %s: %s', user_id, message.content)

        # If the user is mid-way through scheduling, continue that flow.
        if self.scheduler.is_active(user_id):
            await self.scheduler.handle_text(
                user_id, message.content, message.channel
            )
            return

        # Start the scheduling wizard if the user wants to create an event.
        if wants_event(self.conversation.client, message.content):
            logger.info('Starting event wizard for %s.', user_id)
            details: dict = extract_event_details(
                self.conversation.client, message.content
            )
            await self.scheduler.start(user_id, message.channel, details)
            return

        # Track the user's games before and after this message.
        before: set[str] = self.conversation.current_games(user_id)

        # Generate and send the reply.
        async with message.channel.typing():
            reply: str = self.conversation.reply(user_id, message.content)
        if reply:
            logger.info('Reply to %s: %s', user_id, reply)
            await message.channel.send(reply)

        # React to any games the user newly showed interest in.
        after: set[str] = self.conversation.current_games(user_id)
        for game in after - before:
            await self.groups.on_new_interest(user_id, game)


def create_bot() -> GLEM:
    return GLEM()