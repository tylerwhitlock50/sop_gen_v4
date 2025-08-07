from __future__ import annotations

from typing import Dict
from .schemas import ConversationState


class SessionStore:
    """In-memory session store keyed by thread_id.
    Replaceable with persistent cache later.
    """

    def __init__(self) -> None:
        self._store: Dict[str, ConversationState] = {}

    async def get(self, thread_id: str) -> ConversationState | None:
        return self._store.get(thread_id)

    async def set(self, state: ConversationState) -> None:
        self._store[state.thread_id] = state


