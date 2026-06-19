# Import necessary libraries.
from datetime import timedelta
from typing import Awaitable, Callable

import discord


def build_poll(question: str, options: list[str], duration: timedelta
               ) -> discord.Poll:
    # Build a poll.
    poll: discord.Poll = discord.Poll(question=question, duration=duration)
    for option in options:
        poll.add_answer(text=option)
    return poll


def build_buttons(labels: list[str],
                  on_click: Callable[[discord.Interaction, str], Awaitable[None]],
                  ) -> discord.ui.View:
    # Build a view of buttons.
    view: discord.ui.View = discord.ui.View()
    for label in labels:
        button: discord.ui.Button = discord.ui.Button(label=label)

        # Bind the current label into the button callback.
        async def callback(interaction: discord.Interaction, label: str = label):
            await on_click(interaction, label)

        button.callback = callback
        view.add_item(button)
    return view
