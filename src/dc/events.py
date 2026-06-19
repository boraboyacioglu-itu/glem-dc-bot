# Import necessary libraries.
from datetime import datetime

import discord


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
