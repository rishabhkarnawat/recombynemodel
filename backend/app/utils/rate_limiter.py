"""Rate limiter utility placeholders."""

import asyncio


async def exponential_backoff_sleep(attempt: int, base: float = 1.0) -> None:
    """Sleep using exponential backoff for rate limit handling."""

    await asyncio.sleep(base * (2 ** max(0, attempt - 1)))
