from __future__ import annotations

from typing import Any, Dict, List, Literal
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

from .schemas import (
    ConversationState,
    ChatStartRequest,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatAssembleRequest,
    ChatAssembleResponse,
    BlockSnapshot,
)
from .session_store import SessionStore
from .io_tools import write_mermaid_topology, write_mermaid_trace, ensure_artifacts_dir
from .sop_agent import SYSTEM_PROMPT
from . import sop_tools as tools
from api.services.sop_service.document_assembly import DocumentAssembler, DocumentAssemblyConfig, AssemblyFormat


class GraphState(MessagesState):
    thread_id: str
    document_id: int | None
    org_id: int | None
    user_id: int | None
    visited_nodes: List[str]
    open_questions: List[int]


def _classify_intent(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["call", "name", "title"]):
        return "title"
    if any(k in t for k in ["describe", "description", "about"]):
        return "description"
    if any(k in t for k in ["first", "then", "finally", "step"]):
        return "steps"
    return "ambiguous"


def _extract_title(text: str) -> str | None:
    t = text.strip().rstrip(".")
    if len(t.split()) >= 2:
        return t
    return None


def _parse_steps(text: str) -> List[str]:
    parts = [p.strip() for p in text.replace(";", ".").split(".")]
    return [p for p in parts if p]


class ConversationGraph:
    def __init__(self, session_store: SessionStore) -> None:
        self.session_store = session_store
        self.memory = MemorySaver()
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(GraphState)

        async def supervisor(state: GraphState) -> Command[Literal["interviewer", "writer", "researcher", "qc", "__end__"]]:
            # Simple deterministic routing
            last = state["messages"][-1] if state.get("messages") else None
            goto: Literal["interviewer", "writer", "researcher", "qc", "__end__"]
            if not state.get("document_id"):
                goto = "interviewer"
            elif isinstance(last, HumanMessage):
                intent = _classify_intent(last.content)
                if intent in {"title", "description", "steps"}:
                    goto = "writer"
                else:
                    goto = "interviewer"
            else:
                goto = "qc"
            return Command(goto=goto, update={"visited_nodes": state.get("visited_nodes", []) + ["supervisor"]})

        async def interviewer_node(state: GraphState, *, config) -> Command[Literal["supervisor"]]:
            db: AsyncSession = config["db"]
            # Ensure document
            if not state.get("document_id"):
                out = await tools.create_or_get_document(
                    db,
                    tools.CreateOrGetDocumentInput(
                        document_key=None,
                        version=None,
                        document_type="sop",
                        org_id=state.get("org_id") or 1,
                        user_id=state.get("user_id") or 1,
                        document_name="Untitled SOP",
                    ),
                )
                doc_id = out.document_id
            else:
                doc_id = state["document_id"]

            # Ask a single clarifying question
            question = "Hi! Let’s draft a new SOP. What is this process called?" if not state.get("document_id") else "Could you provide a short description or the next steps?"
            # Track question block
            res = await tools.add_question(
                db,
                tools.AddQuestionInput(document_id=doc_id, question=question, user_id=state.get("user_id") or 1),
            )
            oq = state.get("open_questions", []) + [res.block_id]
            return Command(
                update={
                    "document_id": doc_id,
                    "open_questions": oq,
                    "messages": state["messages"] + [AIMessage(content=question)],
                    "visited_nodes": state.get("visited_nodes", []) + ["interviewer"],
                },
                goto="supervisor",
            )

        async def writer_node(state: GraphState, *, config) -> Command[Literal["supervisor"]]:
            db: AsyncSession = config["db"]
            last_human = None
            for m in reversed(state["messages"]):
                if isinstance(m, HumanMessage):
                    last_human = m
                    break
            ack = ""
            if last_human:
                intent = _classify_intent(last_human.content)
                if intent == "title":
                    title = _extract_title(last_human.content) or last_human.content
                    await tools.add_or_update_title(db, tools.AddOrUpdateTitleInput(document_id=state["document_id"], text=title, user_id=state.get("user_id") or 1))
                    ack = "Title captured. Please share a one-sentence description."
                elif intent == "description":
                    await tools.add_or_update_description(db, tools.AddOrUpdateDescriptionInput(document_id=state["document_id"], text=last_human.content, user_id=state.get("user_id") or 1))
                    ack = "Description saved. List the steps briefly."
                elif intent == "steps":
                    steps = _parse_steps(last_human.content)
                    for idx, s in enumerate(steps, 1):
                        await tools.add_or_update_step(db, tools.AddOrUpdateStepInput(document_id=state["document_id"], step_number=idx, step_description=s, user_id=state.get("user_id") or 1))
                    ack = "Steps added. Any PPE or safety warnings to include?"
                else:
                    ack = "Got it. Could you clarify the process name or provide a description?"
            return Command(update={"messages": state["messages"] + [AIMessage(content=ack)], "visited_nodes": state.get("visited_nodes", []) + ["writer"]}, goto="supervisor")

        async def researcher_node(state: GraphState, *, config) -> Command[Literal["supervisor"]]:
            # Look up other SOP titles for hints
            db: AsyncSession = config["db"]
            org_id = state.get("org_id") or 1
            titles_out = await tools.get_all_sop_titles(db, org_id)
            top_titles = ", ".join(titles_out.titles[:5]) if titles_out.titles else "no prior SOPs"
            suggestion = f"Related SOPs in org: {top_titles}. Consider aligning terminology and safety sections."
            return Command(update={"messages": state["messages"] + [AIMessage(content=suggestion)], "visited_nodes": state.get("visited_nodes", []) + ["researcher"]}, goto="supervisor")

        async def qc_node(state: GraphState, *, config) -> Command[Literal["supervisor", "__end__"]]:
            db: AsyncSession = config["db"]
            if not state.get("document_id"):
                return Command(update={}, goto="supervisor")
            pdoc = await tools.load_pydantic_document(db, state["document_id"])
            assembler = DocumentAssembler()
            validation = assembler.validate_document_structure(pdoc)
            if not validation.get("is_valid"):
                missing_block_types = validation.get("missing_required", [])
                # Create QUESTION blocks for each missing type
                for bt in missing_block_types:
                    await tools.add_question(
                        db,
                        tools.AddQuestionInput(
                            document_id=state["document_id"],
                            question=f"Please provide {bt.value}.",
                            user_id=state.get("user_id") or 1,
                        ),
                    )
                missing = ", ".join(bt.value for bt in missing_block_types)
                msg = f"We still need: {missing}. What should we add next?"
                return Command(update={"messages": state["messages"] + [AIMessage(content=msg)], "visited_nodes": state.get("visited_nodes", []) + ["qc"]}, goto="supervisor")
            else:
                msg = "Structure looks complete. Say 'assemble' to generate a preview."
                return Command(update={"messages": state["messages"] + [AIMessage(content=msg)], "visited_nodes": state.get("visited_nodes", []) + ["qc"]}, goto="__end__")

        builder.add_node("supervisor", supervisor)
        builder.add_node("interviewer", interviewer_node)
        builder.add_node("writer", writer_node)
        builder.add_node("researcher", researcher_node)
        builder.add_node("qc", qc_node)
        builder.add_edge(START, "supervisor")
        graph = builder.compile(checkpointer=self.memory)
        return graph

    async def write_static_topology(self) -> str:
        # Programmatically derive from compiled graph
        mermaid = str(self.graph.get_graph().draw_mermaid())
        return write_mermaid_topology(mermaid)

    async def start(self, req: ChatStartRequest, db: AsyncSession) -> ConversationState:
        # Seed memory for thread
        config = {"configurable": {"thread_id": req.thread_id}, "db": db}
        # Kick a supervisor tick to produce a greeting via interviewer
        initial_state: GraphState = {
            "thread_id": req.thread_id,
            "document_id": None,
            "org_id": req.org_id,
            "user_id": req.user_id,
            "messages": [],
            "visited_nodes": [],
            "open_questions": [],
        }
        # Start by routing through supervisor -> interviewer
        self.graph.invoke(initial_state, config=config)
        # Get latest state
        final_state = self.memory.get(config)[1].values if hasattr(self.memory, "get") else initial_state
        # Fallback to reading assistant message from invoke result is non-trivial; return default greeting
        return ConversationState(
            thread_id=req.thread_id,
            document_id=final_state.get("document_id"),
            document_type="sop",
            org_id=req.org_id,
            user_id=req.user_id,
            messages=[{"role": "assistant", "content": "Hi! Let’s draft a new SOP. What is this process called?", "ts": datetime.utcnow().isoformat()}],
        )

    async def handle_message(self, req: ChatMessageRequest, db: AsyncSession) -> ChatMessageResponse:
        config = {"configurable": {"thread_id": req.thread_id}, "db": db}
        # Send user message through graph
        result = self.graph.invoke({"messages": [HumanMessage(content=req.text or "")], "document_id": req.document_id, "org_id": None, "user_id": req.user_id, "visited_nodes": [], "open_questions": []}, config=config)
        # Retrieve accumulated state from memory
        state = self.memory.get(config)[1].values if hasattr(self.memory, "get") else result
        # Snapshot blocks
        if state.get("document_id"):
            blocks_out = await tools.get_document_blocks(db, tools.GetDocumentBlocksInput(document_id=state["document_id"]))
            snapshot = [BlockSnapshot(id=b["id"], type=b["type"], content=b["content"]) for b in blocks_out.blocks]
        else:
            snapshot = []
        # Assistant reply = last AI message
        assistant_text = ""
        for m in reversed(state.get("messages", [])):
            if isinstance(m, AIMessage):
                assistant_text = m.content
                break
        next_hint = "ask_clarification"
        return ChatMessageResponse(
            assistant=assistant_text,
            document_id=state.get("document_id") or 0,
            open_questions=state.get("open_questions", []),
            blocks_snapshot=snapshot,
            next=next_hint,
        )

    async def assemble(self, req: ChatAssembleRequest, db: AsyncSession) -> ChatAssembleResponse:
        config = {"configurable": {"thread_id": req.thread_id}, "db": db}
        ensure_artifacts_dir()
        # compose
        pdoc = await tools.load_pydantic_document(db, req.document_id)
        assembler = DocumentAssembler()
        html_doc = assembler.assemble_document(pdoc, DocumentAssemblyConfig(format_type=AssemblyFormat.HTML, include_toc=True, include_metadata=True))
        md_doc = assembler.assemble_document(pdoc, DocumentAssemblyConfig(format_type=AssemblyFormat.MARKDOWN, include_toc=True, include_metadata=True))
        html_path = f"_artifacts/document_{pdoc.id}_v{pdoc.version}.html"
        md_path = f"_artifacts/document_{pdoc.id}_v{pdoc.version}.md"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_doc.content)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_doc.content)
        # trace
        trace_path = write_mermaid_trace(req.thread_id, ["start", "supervisor", "interviewer", "writer", "qc"])
        # static topology from compiled graph
        mermaid = str(self.graph.get_graph().draw_mermaid())
        topo_path = write_mermaid_topology(mermaid)
        return ChatAssembleResponse(
            preview=html_doc.content,
            html_path=html_path,
            markdown_path=md_path,
            topology_mermaid_path=topo_path,
            trace_mermaid_path=trace_path,
        )
