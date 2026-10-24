import asyncio
import selectors
from typing import Coroutine


def run_async(coro: Coroutine):
    asyncio.run(coro, loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
