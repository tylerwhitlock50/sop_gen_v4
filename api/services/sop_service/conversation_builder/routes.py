from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from api.services.database.db import get_db
from .schemas import (
    ChatStartRequest,
    ChatStartResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatAssembleRequest,
    ChatAssembleResponse,
)
from .session_store import SessionStore
from .sop_graph import ConversationGraph
from .io_tools import ensure_artifacts_dir


router = APIRouter(prefix="/sop/chat", tags=["sop_chat"])
_graph_singleton: ConversationGraph | None = None


@router.on_event("startup")
async def on_startup() -> None:
    ensure_artifacts_dir()
    global _graph_singleton
    _graph_singleton = ConversationGraph(session_store=SessionStore())
    await _graph_singleton.write_static_topology()


@router.post("/start", response_model=ChatStartResponse)
async def start_chat(
    req: ChatStartRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatStartResponse:
    session_store = SessionStore()
    graph = _graph_singleton or ConversationGraph(session_store=session_store)
    state = await graph.start(req, db)
    return ChatStartResponse(
        thread_id=state.thread_id,
        document_id=state.document_id or 0,
        assistant="Hi! Let’s draft a new SOP. What is this process called?",
    )


@router.post("/message", response_model=ChatMessageResponse)
async def post_message(
    req: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    session_store = SessionStore()
    graph = _graph_singleton or ConversationGraph(session_store=session_store)
    result = await graph.handle_message(req, db)
    return result


@router.post("/assemble", response_model=ChatAssembleResponse)
async def assemble(
    req: ChatAssembleRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatAssembleResponse:
    session_store = SessionStore()
    graph = _graph_singleton or ConversationGraph(session_store=session_store)
    result = await graph.assemble(req, db)
    return result


