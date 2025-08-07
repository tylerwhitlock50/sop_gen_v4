from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from api.services.database.models import (
    Document as DocumentModel,
    DocumentBlock as DocumentBlockModel,
    BlockTypeEnum,
    DocumentTypeEnum,
    QuestionStatusEnum,
)
from api.services.sop_service.models.models import (
    Document as PDocument,
    DocumentBlock as PDocumentBlock,
    BlockType as PBlockType,
    DocumentType as PDocumentType,
    DocumentStatus as PDocumentStatus,
)
from api.services.sop_service.document_assembly import (
    DocumentAssembler,
    DocumentAssemblyConfig,
    AssemblyFormat,
)
from .io_tools import write_mermaid_trace


class CreateOrGetDocumentInput(BaseModel):
    document_key: Optional[int] = None
    version: Optional[int] = None
    document_type: str = "sop"
    org_id: int
    user_id: int
    document_name: Optional[str] = None


class CreateOrGetDocumentOutput(BaseModel):
    document_id: int
    version: int


async def create_or_get_document(db: AsyncSession, i: CreateOrGetDocumentInput) -> CreateOrGetDocumentOutput:
    try:
        doc_type = DocumentTypeEnum(i.document_type)
    except Exception:
        doc_type = DocumentTypeEnum.SOP
    if i.document_key:
        stmt = select(DocumentModel).where(DocumentModel.document_key == i.document_key).order_by(DocumentModel.version.desc())
        res = await db.execute(stmt)
        existing = res.scalars().first()
        if existing:
            return CreateOrGetDocumentOutput(document_id=existing.id, version=existing.version)
    # Create
    doc = DocumentModel(
        document_key=i.document_key or int(datetime.now(timezone.utc).timestamp()),
        version=1,
        document_name=i.document_name or "Untitled SOP",
        document_type=doc_type,
        org_id=i.org_id,
        created_by=i.user_id,
        updated_by=i.user_id,
        metadata_json={},
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return CreateOrGetDocumentOutput(document_id=doc.id, version=doc.version)


class AddOrUpdateTitleInput(BaseModel):
    document_id: int
    text: str
    user_id: int


class BlockResult(BaseModel):
    block_id: int


async def add_or_update_title(db: AsyncSession, i: AddOrUpdateTitleInput) -> BlockResult:
    stmt = select(DocumentBlockModel).where(
        (DocumentBlockModel.document_id == i.document_id) & (DocumentBlockModel.block_type == BlockTypeEnum.TITLE)
    ).order_by(DocumentBlockModel.block_order.asc())
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if existing:
        existing.content = {"text": i.text}
        existing.updated_by = i.user_id
        existing.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return BlockResult(block_id=existing.id)
    # else create new at top
    new_block = DocumentBlockModel(
        document_id=i.document_id,
        block_type=BlockTypeEnum.TITLE,
        block_order=1,
        content={"text": i.text},
        created_by=i.user_id,
        updated_by=i.user_id,
    )
    db.add(new_block)
    await db.commit()
    await db.refresh(new_block)
    # shift others down
    # NOTE: keeping simple for now; tests will cover ordering with insertion
    return BlockResult(block_id=new_block.id)


class AddOrUpdateDescriptionInput(BaseModel):
    document_id: int
    text: str
    user_id: int


async def add_or_update_description(db: AsyncSession, i: AddOrUpdateDescriptionInput) -> BlockResult:
    stmt = select(DocumentBlockModel).where(
        (DocumentBlockModel.document_id == i.document_id) & (DocumentBlockModel.block_type == BlockTypeEnum.DESCRIPTION)
    ).order_by(DocumentBlockModel.block_order.asc())
    res = await db.execute(stmt)
    existing = res.scalars().first()
    if existing:
        existing.content = {"text": i.text}
        existing.updated_by = i.user_id
        existing.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return BlockResult(block_id=existing.id)
    # append at end
    order_stmt = select(DocumentBlockModel).where(DocumentBlockModel.document_id == i.document_id).order_by(
        DocumentBlockModel.block_order.desc()
    )
    res2 = await db.execute(order_stmt)
    last = res2.scalars().first()
    new_order = (last.block_order + 1) if last else 1
    new_block = DocumentBlockModel(
        document_id=i.document_id,
        block_type=BlockTypeEnum.DESCRIPTION,
        block_order=new_order,
        content={"text": i.text},
        created_by=i.user_id,
        updated_by=i.user_id,
    )
    db.add(new_block)
    await db.commit()
    await db.refresh(new_block)
    return BlockResult(block_id=new_block.id)


class AddOrUpdateStepInput(BaseModel):
    document_id: int
    step_number: int
    step_description: str
    step_instructions: str = ""
    step_expected_result: str = ""
    step_who_responsible: str = ""
    ppe_required: bool = False
    user_id: int


class StepResult(BaseModel):
    block_id: int
    step_number: int


async def add_or_update_step(db: AsyncSession, i: AddOrUpdateStepInput) -> StepResult:
    # find existing step by step_number in content
    stmt = select(DocumentBlockModel).where(
        (DocumentBlockModel.document_id == i.document_id) & (DocumentBlockModel.block_type == BlockTypeEnum.STEP)
    )
    res = await db.execute(stmt)
    steps = list(res.scalars())
    target = None
    for b in steps:
        if (b.content or {}).get("step_number") == i.step_number:
            target = b
            break
    content = {
        "step_number": i.step_number,
        "step_description": i.step_description,
        "step_instructions": i.step_instructions,
        "step_expected_result": i.step_expected_result,
        "step_who_responsible": i.step_who_responsible,
        "ppe_required": i.ppe_required,
    }
    if target:
        target.content = content
        target.updated_by = i.user_id
        target.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return StepResult(block_id=target.id, step_number=i.step_number)
    # else append at end
    order_stmt = select(DocumentBlockModel).where(DocumentBlockModel.document_id == i.document_id).order_by(
        DocumentBlockModel.block_order.desc()
    )
    res2 = await db.execute(order_stmt)
    last = res2.scalars().first()
    new_order = (last.block_order + 1) if last else 1
    new_block = DocumentBlockModel(
        document_id=i.document_id,
        block_type=BlockTypeEnum.STEP,
        block_order=new_order,
        content=content,
        created_by=i.user_id,
        updated_by=i.user_id,
    )
    db.add(new_block)
    await db.commit()
    await db.refresh(new_block)
    return StepResult(block_id=new_block.id, step_number=i.step_number)


class InsertStepBeforeInput(BaseModel):
    document_id: int
    before_step: int
    step_description: str
    step_instructions: str = ""
    step_expected_result: str = ""
    step_who_responsible: str = ""
    ppe_required: bool = False
    user_id: int


class InsertStepBeforeResult(BaseModel):
    block_id: int
    new_step_number: int


async def insert_step_before(db: AsyncSession, i: InsertStepBeforeInput) -> InsertStepBeforeResult:
    # increment step_number for steps >= before_step
    stmt = select(DocumentBlockModel).where(
        (DocumentBlockModel.document_id == i.document_id) & (DocumentBlockModel.block_type == BlockTypeEnum.STEP)
    )
    res = await db.execute(stmt)
    steps = sorted(list(res.scalars()), key=lambda b: (b.content or {}).get("step_number") or 0)
    for b in steps:
        sn = (b.content or {}).get("step_number")
        if sn is not None and sn >= i.before_step:
            b.content["step_number"] = sn + 1
    # append new step at position before_step
    order_stmt = select(DocumentBlockModel).where(DocumentBlockModel.document_id == i.document_id).order_by(
        DocumentBlockModel.block_order.desc()
    )
    res2 = await db.execute(order_stmt)
    last = res2.scalars().first()
    new_order = (last.block_order + 1) if last else 1
    new_block = DocumentBlockModel(
        document_id=i.document_id,
        block_type=BlockTypeEnum.STEP,
        block_order=new_order,
        content={
            "step_number": i.before_step,
            "step_description": i.step_description,
            "step_instructions": i.step_instructions,
            "step_expected_result": i.step_expected_result,
            "step_who_responsible": i.step_who_responsible,
            "ppe_required": i.ppe_required,
        },
        created_by=i.user_id,
        updated_by=i.user_id,
    )
    db.add(new_block)
    await db.commit()
    await db.refresh(new_block)
    return InsertStepBeforeResult(block_id=new_block.id, new_step_number=i.before_step)


class DeleteStepInput(BaseModel):
    document_id: int
    step_number: int


class DeleteStepResult(BaseModel):
    ok: bool


async def delete_step(db: AsyncSession, i: DeleteStepInput) -> DeleteStepResult:
    stmt = select(DocumentBlockModel).where(
        (DocumentBlockModel.document_id == i.document_id) & (DocumentBlockModel.block_type == BlockTypeEnum.STEP)
    )
    res = await db.execute(stmt)
    steps = list(res.scalars())
    # find target block
    target = None
    for b in steps:
        if (b.content or {}).get("step_number") == i.step_number:
            target = b
            break
    if not target:
        return DeleteStepResult(ok=False)
    await db.delete(target)
    # renumber remaining
    remaining = sorted([b for b in steps if b.id != target.id], key=lambda b: (b.content or {}).get("step_number") or 0)
    for idx, b in enumerate(remaining, 1):
        b.content["step_number"] = idx
    await db.commit()
    return DeleteStepResult(ok=True)


class AddQuestionInput(BaseModel):
    document_id: int
    question: str
    user_id: int


async def add_question(db: AsyncSession, i: AddQuestionInput) -> BlockResult:
    order_stmt = select(DocumentBlockModel).where(DocumentBlockModel.document_id == i.document_id).order_by(
        DocumentBlockModel.block_order.desc()
    )
    res = await db.execute(order_stmt)
    last = res.scalars().first()
    new_order = (last.block_order + 1) if last else 1
    block = DocumentBlockModel(
        document_id=i.document_id,
        block_type=BlockTypeEnum.QUESTION,
        block_order=new_order,
        content={"question": i.question, "status": QuestionStatusEnum.OPEN.value},
        created_by=i.user_id,
        updated_by=i.user_id,
    )
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return BlockResult(block_id=block.id)


class AnswerQuestionInput(BaseModel):
    block_id: int
    answer: str
    answered_by: int


class AnswerQuestionResult(BaseModel):
    block_id: int
    status: str


async def answer_question(db: AsyncSession, i: AnswerQuestionInput) -> AnswerQuestionResult:
    stmt = select(DocumentBlockModel).where(DocumentBlockModel.id == i.block_id)
    res = await db.execute(stmt)
    block = res.scalars().first()
    if not block or block.block_type != BlockTypeEnum.QUESTION:
        raise ValueError("Question block not found")
    c = block.content or {}
    c["answer"] = i.answer
    c["status"] = QuestionStatusEnum.ANSWERED.value
    c["answered_by"] = i.answered_by
    c["answered_at"] = datetime.now(timezone.utc).isoformat()
    block.content = c
    await db.commit()
    return AnswerQuestionResult(block_id=block.id, status=c["status"])


class AddSafetyBlockInput(BaseModel):
    document_id: int
    safety_type: str
    text: str
    user_id: int


async def add_safety_block(db: AsyncSession, i: AddSafetyBlockInput) -> BlockResult:
    mapping = {
        "ppe_required": BlockTypeEnum.PPE_REQUIRED,
        "warning": BlockTypeEnum.WARNING,
        "caution": BlockTypeEnum.CAUTION,
    }
    bt = mapping.get(i.safety_type.lower())
    if not bt:
        raise ValueError("Invalid safety_type")
    order_stmt = select(DocumentBlockModel).where(DocumentBlockModel.document_id == i.document_id).order_by(
        DocumentBlockModel.block_order.desc()
    )
    res = await db.execute(order_stmt)
    last = res.scalars().first()
    new_order = (last.block_order + 1) if last else 1
    block = DocumentBlockModel(
        document_id=i.document_id,
        block_type=bt,
        block_order=new_order,
        content={"text": i.text},
        created_by=i.user_id,
        updated_by=i.user_id,
    )
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return BlockResult(block_id=block.id)


class GetDocumentBlocksInput(BaseModel):
    document_id: int


class GetDocumentBlocksOutput(BaseModel):
    blocks: List[Dict[str, Any]]


async def get_document_blocks(db: AsyncSession, i: GetDocumentBlocksInput) -> GetDocumentBlocksOutput:
    stmt = select(DocumentBlockModel).where(DocumentBlockModel.document_id == i.document_id).order_by(
        DocumentBlockModel.block_order.asc()
    )
    res = await db.execute(stmt)
    blocks = [
        {
            "id": b.id,
            "type": b.block_type.value,
            "block_order": b.block_order,
            "content": b.content,
        }
        for b in res.scalars().all()
    ]
    return GetDocumentBlocksOutput(blocks=blocks)


class GetAllSopTitlesOutput(BaseModel):
    titles: List[str]


async def get_all_sop_titles(db: AsyncSession, org_id: int) -> GetAllSopTitlesOutput:
    stmt = select(DocumentModel).where(DocumentModel.org_id == org_id).order_by(DocumentModel.created_at.desc())
    res = await db.execute(stmt)
    docs = res.scalars().all()
    return GetAllSopTitlesOutput(titles=[d.document_name for d in docs])


class AssembleDocumentInput(BaseModel):
    document_id: int
    format_type: str = "html"
    include_toc: bool = True
    include_metadata: bool = True


class AssembleDocumentOutput(BaseModel):
    path: str
    preview: str


async def assemble_document(db: AsyncSession, i: AssembleDocumentInput) -> AssembleDocumentOutput:
    doc = await load_pydantic_document(db, i.document_id)
    assembler = DocumentAssembler()
    fmt = AssemblyFormat(i.format_type) if i.format_type in [f.value for f in AssemblyFormat] else AssemblyFormat.HTML
    config = DocumentAssemblyConfig(
        format_type=fmt,
        include_toc=i.include_toc,
        include_metadata=i.include_metadata,
    )
    assembled = assembler.assemble_document(doc, config)
    return AssembleDocumentOutput(path="", preview=assembled.content)


class WriteMermaidFromTraceInput(BaseModel):
    thread_id: str
    visited_nodes: List[str]


class WriteMermaidFromTraceOutput(BaseModel):
    path: str


async def write_mermaid_from_trace(i: WriteMermaidFromTraceInput) -> WriteMermaidFromTraceOutput:
    path = write_mermaid_trace(i.thread_id, i.visited_nodes)
    return WriteMermaidFromTraceOutput(path=path)


async def load_pydantic_document(db: AsyncSession, document_id: int) -> PDocument:
    stmt_doc = select(DocumentModel).where(DocumentModel.id == document_id)
    res_doc = await db.execute(stmt_doc)
    d = res_doc.scalars().first()
    if not d:
        raise ValueError("Document not found")
    stmt_blocks = select(DocumentBlockModel).where(DocumentBlockModel.document_id == document_id).order_by(
        DocumentBlockModel.block_order.asc()
    )
    res_blocks = await db.execute(stmt_blocks)
    blocks: List[PDocumentBlock] = []
    for b in res_blocks.scalars().all():
        blocks.append(
            PDocumentBlock(
                id=b.id,
                document_id=b.document_id,
                block_type=PBlockType(b.block_type.value),
                block_order=b.block_order,
                content=b.content,
                metadata_json=b.metadata_json or {},
                created_at=b.created_at,
                updated_at=b.updated_at,
                created_by=b.created_by,
                updated_by=b.updated_by,
                is_active=b.is_active,
            )
        )
    pdoc = PDocument(
        id=d.id,
        document_key=d.document_key,
        version=d.version,
        document_name=d.document_name,
        document_type=PDocumentType(d.document_type.value),
        status=PDocumentStatus(d.status.value),
        org_id=d.org_id,
        created_by=d.created_by,
        updated_by=d.updated_by,
        created_at=d.created_at,
        updated_at=d.updated_at,
        published_at=d.published_at,
        metadata_json=d.metadata_json or {},
        blocks=blocks,
    )
    return pdoc


