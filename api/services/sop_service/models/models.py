from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ───────────────────────────────────────────
# STEP MODEL
# ───────────────────────────────────────────

class SopStepSchema(BaseModel):
    """A model for a SOP step"""
    step_number: int
    step_description: str
    step_instructions: str
    step_expected_result: Optional[str]
    step_who_responsible: Optional[str]
    ppe_required: bool = False
    step_image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True


# ───────────────────────────────────────────
# ENUMS
# ───────────────────────────────────────────

class UserRole(str, Enum):
    ADMIN = 'admin'
    USER = 'user'
    UNLICENSED = 'unlicensed'

class SopStatus(str, Enum):
    USER = 'to_user'
    REVIEWER = 'to_reviewer'
    LAY_REVIEWER = 'to_lay_reviewer'
    APPROVED = 'approved'
    PUBLISHED = 'published'
    DELETED = 'deleted'
    ARCHIVED = 'archived'

class SopQuestionStatus(str, Enum):
    OPEN = 'open'
    ANSWERED = 'answered'
    DECLINED = 'declined'


# ───────────────────────────────────────────
# SUPPORTING MODELS
# ───────────────────────────────────────────

class OrganizationSchema(BaseModel):
    id: int
    organization_name: str
    organization_description: Optional[str]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True

class UserSchema(BaseModel):
    """Model for a user"""
    id: int
    name: str
    email: str
    organization_id: int
    role: UserRole
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True

class SopQuestionSchema(BaseModel):
    """Model for SOP clarifying questions"""
    id: int
    question: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    answered_by: Optional[int] = None
    status: SopQuestionStatus = SopQuestionStatus.OPEN
    answer: Optional[str] = None
    answered_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class SopTagSchema(BaseModel):
    """SOP tag options"""
    id: int
    tag_name: str
    tag_description: Optional[str]
    organization_id: int
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True


# ───────────────────────────────────────────
# MAIN DOCUMENT MODEL
# ───────────────────────────────────────────

class SopDocumentSchema(BaseModel):
    """A model for a SOP document"""
    id: int
    document_key: int  # shared ID across versions
    version: int
    document_name: str
    document_description: str
    steps: List[SopStep] = []
    questions: List[SopQuestion] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: int
    updated_by: int
    status: SopStatus = SopStatus.USER
    tags: Optional[List[str]] = []
    additional_info: Optional[str] = None
    org_id: int
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict)  # flexible context for AI

    class Config:
        orm_mode = True
