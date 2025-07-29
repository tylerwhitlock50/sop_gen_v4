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
from datetime import datetime
import enum

Base = declarative_base()

# ───────────────────────────────────────────
# ENUMS
# ───────────────────────────────────────────

class UserRoleEnum(str, enum.Enum):
    ADMIN = 'admin'
    USER = 'user'
    UNLICENSED = 'unlicensed'

class SopStatusEnum(str, enum.Enum):
    USER = 'to_user'
    REVIEWER = 'to_reviewer'
    LAY_REVIEWER = 'to_lay_reviewer'
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class SopTag(Base):
    __tablename__ = 'sop_tags'

    id = Column(Integer, primary_key=True)
    tag_name = Column(String, nullable=False)
    tag_description = Column(Text)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    created_at = Column(DateTime, default=datetime.utcnow)


class SopDocument(Base):
    __tablename__ = 'sop_documents'

    id = Column(Integer, primary_key=True)
    document_key = Column(Integer, index=True)
    version = Column(Integer)
    document_name = Column(String, nullable=False)
    document_description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    status = Column(Enum(SopStatusEnum), default=SopStatusEnum.USER)
    org_id = Column(Integer, ForeignKey('organizations.id'))
    additional_info = Column(Text)
    metadata_json = Column(JSON, default={})

    steps = relationship("SopStep", cascade="all, delete-orphan", back_populates="document")
    questions = relationship("SopQuestion", cascade="all, delete-orphan", back_populates="document")


class SopStep(Base):
    __tablename__ = 'sop_steps'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('sop_documents.id'))
    step_number = Column(Integer)
    step_description = Column(Text)
    step_instructions = Column(Text)
    step_expected_result = Column(Text)
    step_who_responsible = Column(String)
    ppe_required = Column(Boolean, default=False)
    step_image_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("SopDocument", back_populates="steps")


class SopQuestion(Base):
    __tablename__ = 'sop_questions'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('sop_documents.id'))
    question = Column(Text, nullable=False)
    status = Column(Enum(SopQuestionStatusEnum), default=SopQuestionStatusEnum.OPEN)
    answer = Column(Text)
    answered_by = Column(Integer, ForeignKey('users.id'))
    answered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("SopDocument", back_populates="questions")
