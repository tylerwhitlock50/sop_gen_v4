from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


# ───────────────────────────────────────────
# ENUMS
# ───────────────────────────────────────────

class UserRole(str, Enum):
    ADMIN = 'admin'
    USER = 'user'
    UNLICENSED = 'unlicensed'

class DocumentStatus(str, Enum):
    DRAFT = 'draft'
    TO_USER = 'to_user'
    TO_REVIEWER = 'to_reviewer'
    TO_LAY_REVIEWER = 'to_lay_reviewer'
    APPROVED = 'approved'
    PUBLISHED = 'published'
    DELETED = 'deleted'
    ARCHIVED = 'archived'

class QuestionStatus(str, Enum):
    OPEN = 'open'
    ANSWERED = 'answered'
    DECLINED = 'declined'

class BlockType(str, Enum):
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
    METADATA = 'metadata'
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

class DocumentType(str, Enum):
    SOP = 'sop'
    PROCEDURE = 'procedure'
    WORKFLOW = 'workflow'
    CHECKLIST = 'checklist'
    MANUAL = 'manual'
    POLICY = 'policy'
    GUIDELINE = 'guideline'
    TEMPLATE = 'template'
    OTHER = 'other'

class DocumentTier(str, Enum):
    FREE = 'free'
    PRO = 'pro'
    ENTERPRISE = 'enterprise'
    CUSTOM = 'custom'


# ───────────────────────────────────────────
# BLOCK CONTENT MODELS
# ───────────────────────────────────────────

class BlockContent(BaseModel):
    """Base model for block content - can be extended for specific block types"""
    content: str
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)

class StepBlockContent(BlockContent):
    """Content model for step blocks"""
    step_number: Optional[int] = None
    step_description: Optional[str] = None
    step_instructions: Optional[str] = None
    step_expected_result: Optional[str] = None
    step_who_responsible: Optional[str] = None
    ppe_required: bool = False
    step_image_url: Optional[str] = None

class QuestionBlockContent(BlockContent):
    """Content model for question blocks"""
    question: str
    status: QuestionStatus = QuestionStatus.OPEN
    answer: Optional[str] = None
    answered_by: Optional[int] = None
    answered_at: Optional[datetime] = None

class ImageBlockContent(BlockContent):
    """Content model for image blocks"""
    image_url: str
    alt_text: Optional[str] = None
    caption: Optional[str] = None

class ChecklistBlockContent(BlockContent):
    """Content model for checklist blocks"""
    items: List[Dict[str, Any]] = Field(default_factory=list)
    allow_multiple: bool = False

class RiskAssessmentBlockContent(BlockContent):
    """Content model for risk assessment blocks"""
    risks: List[Dict[str, Any]] = Field(default_factory=list)
    controls: List[Dict[str, Any]] = Field(default_factory=list)
    risk_matrix: Optional[Dict[str, Any]] = None


# ───────────────────────────────────────────
# BLOCK MODEL
# ───────────────────────────────────────────

class DocumentBlock(BaseModel):
    """A flexible block model for document content"""
    id: int
    document_id: int
    block_type: BlockType
    block_order: int  # For ordering blocks within a document
    content: Union[str, Dict[str, Any]]  # Flexible content storage
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: int
    updated_by: int
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


# ───────────────────────────────────────────
# DOCUMENT MODEL
# ───────────────────────────────────────────

class Document(BaseModel):
    """A flexible document model that uses blocks for content"""
    id: int
    document_key: int  # Shared ID across versions
    version: int
    document_name: str
    document_type: DocumentType
    document_tier: DocumentTier = DocumentTier.FREE
    status: DocumentStatus = DocumentStatus.DRAFT
    org_id: int
    created_by: int
    updated_by: int
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)
    blocks: List[DocumentBlock] = []

    model_config = ConfigDict(from_attributes=True)


# ───────────────────────────────────────────
# SUPPORTING MODELS
# ───────────────────────────────────────────

class Organization(BaseModel):
    id: int
    organization_name: str
    organization_description: Optional[str]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)

class User(BaseModel):
    """Model for a user"""
    id: int
    name: str
    email: str
    organization_id: int
    role: UserRole
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)

class Tag(BaseModel):
    """Document tag model"""
    id: int
    tag_name: str
    tag_description: Optional[str]
    organization_id: int
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


# ───────────────────────────────────────────
# ASSEMBLY MODELS (for document generation)
# ───────────────────────────────────────────

class DocumentAssemblyConfig(BaseModel):
    """Configuration for document assembly"""
    include_toc: bool = True
    include_metadata: bool = True
    include_tags: bool = True
    format_type: str = "html"  # html, pdf, markdown, etc.
    template_name: Optional[str] = None

class AssembledDocument(BaseModel):
    """Result of document assembly"""
    document_id: int
    content: str
    format_type: str
    assembled_at: datetime = Field(default_factory=datetime.now)
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)
