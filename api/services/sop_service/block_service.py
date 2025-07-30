# api/services/sop_service/block_service.py
# Service for managing blocks within documents

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models.models import (
    Document, DocumentBlock, BlockType, DocumentStatus, 
    StepBlockContent, QuestionBlockContent, ImageBlockContent,
    ChecklistBlockContent, RiskAssessmentBlockContent
)
from ..database.models import Document as DocumentModel, DocumentBlock as DocumentBlockModel


class BlockService:
    """Service for managing blocks within documents"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def add_block(
        self, 
        document_id: int, 
        block_type: BlockType, 
        content: Union[str, Dict[str, Any]], 
        created_by: int,
        position: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentBlock:
        """
        Add a new block to a document
        
        Args:
            document_id: ID of the document
            block_type: Type of block to add
            content: Block content (string or dict)
            created_by: User ID who created the block
            position: Optional position to insert at (defaults to end)
            metadata: Optional metadata for the block
            
        Returns:
            Created block
        """
        # Validate document exists
        document = self.db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")
        
        # Determine block order
        if position is None:
            # Add to end
            max_order = self.db.query(DocumentBlockModel.block_order)\
                .filter(DocumentBlockModel.document_id == document_id)\
                .order_by(DocumentBlockModel.block_order.desc())\
                .first()
            block_order = (max_order[0] + 1) if max_order else 1
        else:
            # Insert at specific position
            self._reorder_blocks_for_insert(document_id, position)
            block_order = position
        
        # Create block
        block = DocumentBlockModel(
            document_id=document_id,
            block_type=block_type.value,
            block_order=block_order,
            content=content if isinstance(content, dict) else {"text": content},
            metadata=metadata or {},
            created_by=created_by,
            updated_by=created_by
        )
        
        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)
        
        return self._convert_to_pydantic(block)
    
    def update_block(
        self, 
        block_id: int, 
        content: Union[str, Dict[str, Any]], 
        updated_by: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentBlock:
        """
        Update an existing block
        
        Args:
            block_id: ID of the block to update
            content: New content for the block
            updated_by: User ID who updated the block
            metadata: Optional new metadata
            
        Returns:
            Updated block
        """
        block = self.db.query(DocumentBlockModel).filter(DocumentBlockModel.id == block_id).first()
        if not block:
            raise ValueError(f"Block with ID {block_id} not found")
        
        block.content = content if isinstance(content, dict) else {"text": content}
        block.updated_by = updated_by
        block.updated_at = datetime.now(timezone.utc)
        
        if metadata is not None:
            block.metadata_json = metadata
        
        self.db.commit()
        self.db.refresh(block)
        
        return self._convert_to_pydantic(block)
    
    def delete_block(self, block_id: int) -> bool:
        """
        Delete a block from a document
        
        Args:
            block_id: ID of the block to delete
            
        Returns:
            True if deleted successfully
        """
        block = self.db.query(DocumentBlockModel).filter(DocumentBlockModel.id == block_id).first()
        if not block:
            raise ValueError(f"Block with ID {block_id} not found")
        
        document_id = block.document_id
        
        # Delete the block
        self.db.delete(block)
        
        # Reorder remaining blocks
        self._reorder_blocks_after_delete(document_id)
        
        self.db.commit()
        return True
    
    def reorder_blocks(self, document_id: int, block_orders: List[Dict[str, int]]) -> List[DocumentBlock]:
        """
        Reorder blocks in a document
        
        Args:
            document_id: ID of the document
            block_orders: List of {block_id: new_order} mappings
            
        Returns:
            Updated blocks in new order
        """
        # Validate document exists
        document = self.db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")
        
        # Update block orders
        for block_order in block_orders:
            block_id = block_order.get("block_id")
            new_order = block_order.get("order")
            
            if block_id and new_order:
                block = self.db.query(DocumentBlockModel).filter(DocumentBlockModel.id == block_id).first()
                if block:
                    block.block_order = new_order
                    block.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        # Return blocks in new order
        blocks = self.db.query(DocumentBlockModel)\
            .filter(DocumentBlockModel.document_id == document_id)\
            .order_by(DocumentBlockModel.block_order)\
            .all()
        
        return [self._convert_to_pydantic(block) for block in blocks]
    
    def get_document_blocks(self, document_id: int) -> List[DocumentBlock]:
        """
        Get all blocks for a document in order
        
        Args:
            document_id: ID of the document
            
        Returns:
            List of blocks in order
        """
        blocks = self.db.query(DocumentBlockModel)\
            .filter(and_(
                DocumentBlockModel.document_id == document_id,
                DocumentBlockModel.is_active == True
            ))\
            .order_by(DocumentBlockModel.block_order)\
            .all()
        
        return [self._convert_to_pydantic(block) for block in blocks]
    
    def get_block(self, block_id: int) -> Optional[DocumentBlock]:
        """
        Get a specific block by ID
        
        Args:
            block_id: ID of the block
            
        Returns:
            Block if found, None otherwise
        """
        block = self.db.query(DocumentBlockModel).filter(DocumentBlockModel.id == block_id).first()
        return self._convert_to_pydantic(block) if block else None
    
    def duplicate_block(self, block_id: int, created_by: int) -> DocumentBlock:
        """
        Duplicate a block
        
        Args:
            block_id: ID of the block to duplicate
            created_by: User ID who created the duplicate
            
        Returns:
            New duplicated block
        """
        original_block = self.db.query(DocumentBlockModel).filter(DocumentBlockModel.id == block_id).first()
        if not original_block:
            raise ValueError(f"Block with ID {block_id} not found")
        
        # Create new block with same content but new order
        max_order = self.db.query(DocumentBlockModel.block_order)\
            .filter(DocumentBlockModel.document_id == original_block.document_id)\
            .order_by(DocumentBlockModel.block_order.desc())\
            .first()
        
        new_order = (max_order[0] + 1) if max_order else 1
        
        new_block = DocumentBlockModel(
            document_id=original_block.document_id,
            block_type=original_block.block_type,
            block_order=new_order,
            content=original_block.content.copy() if isinstance(original_block.content, dict) else original_block.content,
            metadata_json=original_block.metadata_json.copy() if original_block.metadata_json else {},
            created_by=created_by,
            updated_by=created_by
        )
        
        self.db.add(new_block)
        self.db.commit()
        self.db.refresh(new_block)
        
        return self._convert_to_pydantic(new_block)
    
    def add_step_block(
        self, 
        document_id: int, 
        step_content: StepBlockContent, 
        created_by: int,
        position: Optional[int] = None
    ) -> DocumentBlock:
        """
        Add a step block with structured content
        
        Args:
            document_id: ID of the document
            step_content: Structured step content
            created_by: User ID who created the block
            position: Optional position to insert at
            
        Returns:
            Created step block
        """
        content = step_content.model_dump()
        return self.add_block(
            document_id=document_id,
            block_type=BlockType.STEP,
            content=content,
            created_by=created_by,
            position=position
        )
    
    def add_question_block(
        self, 
        document_id: int, 
        question_content: QuestionBlockContent, 
        created_by: int,
        position: Optional[int] = None
    ) -> DocumentBlock:
        """
        Add a question block with structured content
        
        Args:
            document_id: ID of the document
            question_content: Structured question content
            created_by: User ID who created the block
            position: Optional position to insert at
            
        Returns:
            Created question block
        """
        content = question_content.model_dump()
        return self.add_block(
            document_id=document_id,
            block_type=BlockType.QUESTION,
            content=content,
            created_by=created_by,
            position=position
        )
    
    def add_image_block(
        self, 
        document_id: int, 
        image_content: ImageBlockContent, 
        created_by: int,
        position: Optional[int] = None
    ) -> DocumentBlock:
        """
        Add an image block with structured content
        
        Args:
            document_id: ID of the document
            image_content: Structured image content
            created_by: User ID who created the block
            position: Optional position to insert at
            
        Returns:
            Created image block
        """
        content = image_content.model_dump()
        return self.add_block(
            document_id=document_id,
            block_type=BlockType.IMAGE,
            content=content,
            created_by=created_by,
            position=position
        )
    
    def add_checklist_block(
        self, 
        document_id: int, 
        checklist_content: ChecklistBlockContent, 
        created_by: int,
        position: Optional[int] = None
    ) -> DocumentBlock:
        """
        Add a checklist block with structured content
        
        Args:
            document_id: ID of the document
            checklist_content: Structured checklist content
            created_by: User ID who created the block
            position: Optional position to insert at
            
        Returns:
            Created checklist block
        """
        content = checklist_content.model_dump()
        return self.add_block(
            document_id=document_id,
            block_type=BlockType.CHECKLIST,
            content=content,
            created_by=created_by,
            position=position
        )
    
    def _reorder_blocks_for_insert(self, document_id: int, position: int):
        """Reorder blocks to make room for insertion at position"""
        blocks_to_update = self.db.query(DocumentBlockModel)\
            .filter(and_(
                DocumentBlockModel.document_id == document_id,
                DocumentBlockModel.block_order >= position
            ))\
            .all()
        
        for block in blocks_to_update:
            block.block_order += 1
            block.updated_at = datetime.now(timezone.utc)
    
    def _reorder_blocks_after_delete(self, document_id: int):
        """Reorder blocks after deletion to maintain sequential order"""
        blocks = self.db.query(DocumentBlockModel)\
            .filter(DocumentBlockModel.document_id == document_id)\
            .order_by(DocumentBlockModel.block_order)\
            .all()
        
        for i, block in enumerate(blocks, 1):
            if block.block_order != i:
                block.block_order = i
                block.updated_at = datetime.now(timezone.utc)
    
    def _convert_to_pydantic(self, db_block: DocumentBlockModel) -> DocumentBlock:
        """Convert SQLAlchemy model to Pydantic model"""
        return DocumentBlock(
            id=db_block.id,
            document_id=db_block.document_id,
            block_type=BlockType(db_block.block_type),
            block_order=db_block.block_order,
            content=db_block.content,
            metadata=db_block.metadata_json,
            created_at=db_block.created_at,
            updated_at=db_block.updated_at,
            created_by=db_block.created_by,
            updated_by=db_block.updated_by,
            is_active=db_block.is_active
        ) 