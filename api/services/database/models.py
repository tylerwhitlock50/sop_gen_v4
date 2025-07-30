# api/services/database/models.py
# This file is used to create the models for the database
# It uses the sqlalchemy library to create the models
# It uses the sqlalchemy.orm library to create the relationships
# It uses the sqlalchemy.ext.declarative library to create the base model
# It uses the sqlalchemy.ext.asyncio library to create the asynchronous session
# It uses the sqlalchemy.ext.asyncio library to create the asynchronous engine
# It uses the sqlalchemy.ext.asyncio library to create the asynchronous session
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Enum, ForeignKey, Table, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone
import enum

Base = declarative_base()

# ───────────────────────────────────────────
# ENUMS
# ───────────────────────────────────────────

class UserRoleEnum(str, enum.Enum):
    ADMIN = 'admin'
    USER = 'user'
    UNLICENSED = 'unlicensed'

class DocumentStatusEnum(str, enum.Enum):
    DRAFT = 'draft'
    TO_USER = 'to_user'
    TO_REVIEWER = 'to_reviewer'
    TO_LAY_REVIEWER = 'to_lay_reviewer'
    APPROVED = 'approved'
    PUBLISHED = 'published'
    DELETED = 'deleted'
    ARCHIVED = 'archived'

class QuestionStatusEnum(str, enum.Enum):
    OPEN = 'open'
    ANSWERED = 'answered'
    DECLINED = 'declined'

class BlockTypeEnum(str, enum.Enum):
    # Basic content blocks
    TITLE = 'title'
    DESCRIPTION = 'description'
    SECTION_HEADER = 'section_header'
    PARAGRAPH = 'paragraph'
    
    # Step-related blocks
    STEP = 'step'
    STEP_GROUP = 'step_group'
    STEP_INSTRUCTION = 'step_instruction'
    STEP_RESULT = 'step_result'
    STEP_RESPONSIBLE = 'step_responsible'
    
    # Question blocks
    QUESTION = 'question'
    QUESTION_GROUP = 'question_group'
    
    # Metadata blocks
    TAGS = 'tags'
    TAG = 'tag'
    METADATA_BLOCK = 'metadata'
    ADDITIONAL_INFO = 'additional_info'
    
    # Safety and compliance blocks
    PPE_REQUIRED = 'ppe_required'
    SAFETY_NOTICE = 'safety_notice'
    WARNING = 'warning'
    CAUTION = 'caution'
    
    # Risk and control blocks
    RISK_ASSESSMENT = 'risk_assessment'
    CONTROL_ASSESSMENT = 'control_assessment'
    CONTROL_MATRIX = 'control_matrix'
    RISKS = 'risks'
    CONTROLS = 'controls'
    
    # Document structure blocks
    TABLE_OF_CONTENTS = 'table_of_contents'
    APPENDIX = 'appendix'
    REFERENCE = 'reference'
    
    # Media blocks
    IMAGE = 'image'
    VIDEO = 'video'
    ATTACHMENT = 'attachment'
    
    # Interactive blocks
    CHECKLIST = 'checklist'
    FORM = 'form'
    SIGNATURE = 'signature'

class DocumentTypeEnum(str, enum.Enum):
    SOP = 'sop'
    PROCEDURE = 'procedure'
    WORKFLOW = 'workflow'
    CHECKLIST = 'checklist'
    MANUAL = 'manual'
    POLICY = 'policy'
    GUIDELINE = 'guideline'
    TEMPLATE = 'template'
    OTHER = 'other'

class DocumentTierEnum(str, enum.Enum):
    FREE = 'free'
    PRO = 'pro'
    ENTERPRISE = 'enterprise'
    CUSTOM = 'custom'

# Legacy enums for backward compatibility
class SopStatusEnum(str, enum.Enum):
    TO_USER = 'to_user'
    TO_REVIEWER = 'to_reviewer'
    TO_LAY_REVIEWER = 'to_lay_reviewer'
    APPROVED = 'approved'
    PUBLISHED = 'published'
    DELETED = 'deleted'
    ARCHIVED = 'archived'

class SopQuestionStatusEnum(str, enum.Enum):
    OPEN = 'open'
    ANSWERED = 'answered'
    DECLINED = 'declined'

# ───────────────────────────────────────────
# MODELS
# ───────────────────────────────────────────

class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True)
    organization_name = Column(String, nullable=False)
    organization_description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    tag_name = Column(String, nullable=False)
    tag_description = Column(Text)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ───────────────────────────────────────────
# NEW FLEXIBLE DOCUMENT MODELS
# ───────────────────────────────────────────

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    document_key = Column(Integer, index=True)  # Shared ID across versions
    version = Column(Integer, default=1)
    document_name = Column(String, nullable=False)
    document_type = Column(Enum(DocumentTypeEnum), nullable=False)
    document_tier = Column(Enum(DocumentTierEnum), default=DocumentTierEnum.FREE)
    status = Column(Enum(DocumentStatusEnum), default=DocumentStatusEnum.DRAFT)
    org_id = Column(Integer, ForeignKey('organizations.id'))
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime)
    metadata_json = Column(JSON, default={})

    # Relationships
    blocks = relationship("DocumentBlock", cascade="all, delete-orphan", back_populates="document", order_by="DocumentBlock.block_order")
    tags = relationship("DocumentTag", cascade="all, delete-orphan", back_populates="document")


class DocumentBlock(Base):
    __tablename__ = 'document_blocks'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    block_type = Column(Enum(BlockTypeEnum), nullable=False)
    block_order = Column(Integer, nullable=False)  # For ordering blocks within a document
    content = Column(JSON, nullable=False)  # Flexible content storage as JSON
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    is_active = Column(Boolean, default=True)

    # Relationships
    document = relationship("Document", back_populates="blocks")


class DocumentTag(Base):
    __tablename__ = 'document_tags'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'))
    tag_id = Column(Integer, ForeignKey('tags.id'))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    document = relationship("Document", back_populates="tags")
    tag = relationship("Tag")

