"""Shared ML lock to serialize Ollama access on constrained hardware."""

import asyncio

from app.config import settings

ml_lock = asyncio.Lock()


class MLMutex:
    """Context manager that optionally acquires the shared ML lock."""

    def __init__(self) -> None:
        self._enabled = settings.ml_mutex_enabled
        self._acquired = False

    async def __aenter__(self) -> "MLMutex":
        if self._enabled:
            await ml_lock.acquire()
            self._acquired = True
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._acquired:
            ml_lock.release()


def is_ml_busy() -> bool:
    return ml_lock.locked()
