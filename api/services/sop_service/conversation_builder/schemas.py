from __future__ import annotations

from typing import Any, List, Dict, Optional
from pydantic import BaseModel, Field


class ChatStartRequest(BaseModel):
    thread_id: str
    document_key: Optional[int] = None
    document_type: str = "sop"
    document_name: Optional[str] = None
    org_id: int
    user_id: int


class ChatStartResponse(BaseModel):
    thread_id: str
    document_id: int
    assistant: str


class ChatMessageRequest(BaseModel):
    thread_id: str
    document_id: Optional[int] = None
    user_id: int
    text: Optional[str] = None
    audio_b64: Optional[str] = None
    assemble: bool = False


class BlockSnapshot(BaseModel):
    id: int
    type: str
    content: Dict[str, Any]


class ChatMessageResponse(BaseModel):
    assistant: str
    document_id: int
    open_questions: List[int] = Field(default_factory=list)
    blocks_snapshot: List[BlockSnapshot] = Field(default_factory=list)
    next: str


class ChatAssembleRequest(BaseModel):
    thread_id: str
    document_id: int
    format: str = "html"


class ChatAssembleResponse(BaseModel):
    preview: str
    html_path: Optional[str] = None
    markdown_path: Optional[str] = None
    topology_mermaid_path: str
    trace_mermaid_path: str


class ConversationState(BaseModel):
    thread_id: str
    document_id: Optional[int] = None
    document_type: str = "sop"
    org_id: Optional[int] = None
    user_id: Optional[int] = None
    messages: List[Dict[str, Any]] = Field(default_factory=list)  # {role, content, ts}
    open_questions: List[int] = Field(default_factory=list)
    required_block_gaps: List[str] = Field(default_factory=list)
    step_index: Dict[int, int] = Field(default_factory=dict)  # step_number -> block_id
    visited_nodes: List[str] = Field(default_factory=list)


