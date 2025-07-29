from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.services.database.models import SopDocument
from api.services.sop_service.models import * 
from typing import Optional
from api.services.logger import logger
from api.services.database import get_db

class SopService:
    def __init__(self, document_key: Optional[int] = None, version: Optional[int] = None):
        self.document_key = document_key
        self.version = version
        logger.info(f"SOP Service initialized with document key: {self.document_key} and version: {self.version}")
    
    async def get_sop_document(self, db: AsyncSession) -> Optional[SopDocument]:
        """Get the latest SOP document by document key"""
        if not self.document_key:
            return None
        
        stmt = select(SopDocument).where(SopDocument.document_key == self.document_key)

        if self.version:
            stmt = stmt.where(SopDocument.version == self.version)
        else:
            stmt = stmt.order_by(SopDocument.version.desc()).limit(1)
            
        result = await db.execute(stmt)
        sop_row = result.scalar_one_or_none()
        if sop_row:
            return SopDocument.model_validate(sop_row)
        return None
    
    async def create_sop_document(self, db: AsyncSession, document: SopDocument) -> SopDocument:
        """Create a new SOP document"""
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document
    
    async def update_sop_document(self, db: AsyncSession, document: SopDocument) -> SopDocument:
        """Update a SOP document"""
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document
    