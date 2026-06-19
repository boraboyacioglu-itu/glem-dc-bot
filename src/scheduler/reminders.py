# Import necessary libraries.
import asyncio
from datetime import datetime, timezone
from typing import Callable, Awaitable

# A reminder callback takes no arguments and runs asynchronously.
Reminder = Callable[[], Awaitable[None]]


def schedule_in(delay: float, callback: Reminder) -> asyncio.Task:
    # Schedule the callback to run after the given delay in seconds.
    async def runner():
        await asyncio.sleep(delay)
        await callback()

    return asyncio.create_task(runner())


def schedule_at(when: datetime, callback: Reminder) -> asyncio.Task:
    # Schedule the callback to run at the given moment in time.
    now: datetime = datetime.now(timezone.utc)
    delay: float = max(0.0, (when - now).total_seconds())
    return schedule_in(delay, callback)
