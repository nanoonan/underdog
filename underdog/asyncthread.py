import asyncio
import concurrent
import enum
import logging
import threading
import time

from typing import (
    Any, Awaitable, cast
)

logger = logging.getLogger(__name__)

class AsyncThreadState(enum.Enum):
    Created = 1
    Started = 2
    Stopped = 3

class AsyncThread(threading.Thread):

    def __init__(self) -> None:
        super().__init__()
        self._loop: Any = None
        self._state: AsyncThreadState = AsyncThreadState.Created

    @property
    def state(self) -> AsyncThreadState:
        return self._state

    def start(self) -> None:
        assert self._state == AsyncThreadState.Created
        super().start()
        while self._loop is None or not self._loop.is_running():
            time.sleep(0)
        self._state = AsyncThreadState.Started

    async def _stop_(self) -> None:
        try:
            tasks = []
            for task in asyncio.all_tasks():
                if task != asyncio.current_task():
                    tasks.append(task)
                    task.cancel()
            if tasks:
                await asyncio.wait(tasks)
        finally:
            pass
            # commented out because closing causes error in windows destructor
            # self._loop.stop()

    def run_task(
        self,
        coro: Awaitable[Any],
        block: bool = True
    ) -> Any:
        assert self._state == AsyncThreadState.Started
        if not block:
            return asyncio.run_coroutine_threadsafe(coro, self._loop)
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        concurrent.futures.wait([future])
        assert future.done()
        if future.exception() is not None:
            raise cast(BaseException, future.exception())
        return future.result()

    def stop(self) -> None:
        assert self._state == AsyncThreadState.Started
        future = asyncio.run_coroutine_threadsafe(self._stop_(), self._loop)
        concurrent.futures.wait([future])
        assert future.done()
        self._state = AsyncThreadState.Stopped
        if future.exception() is not None:
            raise cast(BaseException, future.exception())
        return future.result()

    def run(self) -> None:
        try:
            self._loop = asyncio.new_event_loop()
            self._loop.run_forever()
        finally:
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            # commented out because closing causes error in windows destructor
            # self._loop.close()
