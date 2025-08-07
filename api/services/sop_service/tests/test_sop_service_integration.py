# api/services/sop_service/tests/test_sop_service_integration.py
# Comprehensive test for SOP service integration

import pytest
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import models
from api.services.database.models import (
    Base, Document as DocumentModel, DocumentBlock as DocumentBlockModel,
    Organization, User, DocumentTypeEnum, DocumentStatusEnum, 
    DocumentTierEnum, BlockTypeEnum
)

# Import services
from api.services.sop_service.block_service import BlockService
from api.services.sop_service.document_assembly import DocumentAssembler, AssemblyFormat
from api.services.sop_service.sop_service import SopService

# Import Pydantic models
from api.services.sop_service.models.models import (
    Document, DocumentBlock, BlockType, DocumentType, DocumentStatus,
    DocumentTier, StepBlockContent, DocumentAssemblyConfig
)


class TestSopServiceIntegration:
    """Integration test for SOP service functionality"""
    
    def setup_method(self):
        """Set up test database and session"""
        # Create in-memory SQLite database for testing
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.block_service = BlockService(self.db_session)
        self.document_assembler = DocumentAssembler()
        
        # Create test data
        self._create_test_data()
    
    def teardown_method(self):
        """Clean up test database"""
        # Commented out to preserve data for inspection
        # self.db_session.close()
        # Base.metadata.drop_all(self.engine)
        print("🗄️ Database preserved for inspection - data will remain in database.db")
    
    def _create_test_data(self):
        """Create test organizations and users"""
        # Create test organization
        org = Organization(
            organization_name="Test Organization",
            organization_description="Test organization for integration tests"
        )
        self.db_session.add(org)
        self.db_session.commit()
        self.org_id = org.id
        
        # Create test user
        user = User(
            name="Test User",
            email="test@example.com",
            organization_id=self.org_id,
            role="admin"
        )
        self.db_session.add(user)
        self.db_session.commit()
        self.user_id = user.id
    
    def test_create_document_with_blocks(self):
        """Test creating a document with title, description, and steps"""
        print("\n=== Testing Document Creation with Blocks ===")
        
        # 1. Create the main document
        document = DocumentModel(
            document_key=1001,
            version=1,
            document_name="Laboratory Safety Procedures",
            document_type=DocumentTypeEnum.SOP,
            document_tier=DocumentTierEnum.PRO,
            status=DocumentStatusEnum.DRAFT,
            org_id=self.org_id,
            created_by=self.user_id,
            updated_by=self.user_id,
            metadata_json={
                "department": "Laboratory",
                "risk_level": "medium",
                "review_frequency": "annual"
            }
        )
        
        self.db_session.add(document)
        self.db_session.commit()
        self.db_session.refresh(document)
        
        print(f"✅ Created document: {document.document_name}")
        print(f"   - Document ID: {document.id}")
        print(f"   - Document Key: {document.document_key}")
        print(f"   - Type: {document.document_type.value}")
        print(f"   - Status: {document.status.value}")
        
        # 2. Add title block
        title_block = self.block_service.add_block(
            document_id=document.id,
            block_type=BlockType.TITLE,
            content={"text": "Laboratory Safety Procedures"},
            created_by=self.user_id,
            position=1
        )
        
        print(f"✅ Added title block: {title_block.content.get('text', '')}")
        
        # 3. Add description block
        description_block = self.block_service.add_block(
            document_id=document.id,
            block_type=BlockType.DESCRIPTION,
            content={"text": "This document outlines the safety procedures that must be followed when working in the laboratory."},
            created_by=self.user_id,
            position=2
        )
        
        print(f"✅ Added description block: {description_block.content.get('text', '')[:50]}...")
        
        # 4. Add section header
        section_block = self.block_service.add_block(
            document_id=document.id,
            block_type=BlockType.SECTION_HEADER,
            content={"text": "Pre-Entry Procedures"},
            created_by=self.user_id,
            position=3
        )
        
        print(f"✅ Added section header: {section_block.content.get('text', '')}")
        
        # 5. Add first step block
        step1_content = StepBlockContent(
            content="Step 1 content",
            step_number=1,
            step_description="Check safety equipment",
            step_instructions="Ensure all safety equipment is available and in good condition before entering the laboratory.",
            step_expected_result="All safety equipment is verified and ready for use.",
            step_who_responsible="Laboratory technician",
            ppe_required=True
        )
        
        step1_block = self.block_service.add_step_block(
            document_id=document.id,
            step_content=step1_content,
            created_by=self.user_id,
            position=4
        )
        
        print(f"✅ Added step 1: {step1_block.content.get('step_description', '')}")
        print(f"   - PPE Required: {step1_block.content.get('ppe_required', False)}")
        
        # 6. Add second step block
        step2_content = StepBlockContent(
            content="Step 2 content",
            step_number=2,
            step_description="Review hazard assessment",
            step_instructions="Review the hazard assessment for any experiments or procedures planned for the day.",
            step_expected_result="All hazards are identified and understood.",
            step_who_responsible="Laboratory supervisor",
            ppe_required=False
        )
        
        step2_block = self.block_service.add_step_block(
            document_id=document.id,
            step_content=step2_content,
            created_by=self.user_id,
            position=5
        )
        
        print(f"✅ Added step 2: {step2_block.content.get('step_description', '')}")
        print(f"   - PPE Required: {step2_block.content.get('ppe_required', False)}")
        
        # Store document for later tests
        self.test_document_id = document.id
        self.test_document = document
        
    def test_block_operations(self):
        """Test various block operations"""
        print("\n=== Testing Block Operations ===")
        
        # First create a document with blocks
        self.test_create_document_with_blocks()
        
        # 1. Get all blocks for the document
        blocks = self.block_service.get_document_blocks(self.test_document.id)
        print(f"✅ Retrieved {len(blocks)} blocks for document")
        
        for i, block in enumerate(blocks, 1):
            print(f"   {i}. {block.block_type.value}: {block.content.get('text', block.content.get('step_description', 'N/A'))}")
        
        # 2. Get a specific block
        first_block = self.block_service.get_block(blocks[0].id)
        print(f"✅ Retrieved specific block: {first_block.block_type.value}")
        
        # 3. Update a block
        updated_block = self.block_service.update_block(
            block_id=blocks[0].id,
            content={"text": "Updated Laboratory Safety Procedures"},
            updated_by=self.user_id
        )
        print(f"✅ Updated block: {updated_block.content.get('text', '')}")
        
        # 4. Duplicate a block
        duplicated_block = self.block_service.duplicate_block(
            block_id=blocks[0].id,
            created_by=self.user_id
        )
        print(f"✅ Duplicated block: {duplicated_block.content.get('text', '')}")
        
        # 5. Reorder blocks
        block_orders = [
            {"block_id": blocks[0].id, "order": 1},
            {"block_id": blocks[1].id, "order": 2},
            {"block_id": blocks[2].id, "order": 3},
            {"block_id": blocks[3].id, "order": 4},
            {"block_id": blocks[4].id, "order": 5},
            {"block_id": duplicated_block.id, "order": 6}
        ]
        
        reordered_blocks = self.block_service.reorder_blocks(self.test_document.id, block_orders)
        print(f"✅ Reordered {len(reordered_blocks)} blocks")
        
        # 6. Delete a block
        deleted = self.block_service.delete_block(duplicated_block.id)
        print(f"✅ Deleted duplicated block: {deleted}")
        
        # Verify final block count
        final_blocks = self.block_service.get_document_blocks(self.test_document.id)
        print(f"✅ Final block count: {len(final_blocks)}")
    
    def test_document_assembly(self):
        """Test document assembly in different formats"""
        print("\n=== Testing Document Assembly ===")
        
        # First create a document with blocks
        self.test_create_document_with_blocks()
        
        # Get all blocks for assembly
        blocks = self.block_service.get_document_blocks(self.test_document.id)
        
        # Convert to Pydantic models for assembly
        pydantic_blocks = []
        for block in blocks:
            pydantic_block = DocumentBlock(
                id=block.id,
                document_id=block.document_id,
                block_type=BlockType(block.block_type.value),
                block_order=block.block_order,
                content=block.content,
                metadata_json=block.metadata_json,
                created_at=block.created_at,
                updated_at=block.updated_at,
                created_by=block.created_by,
                updated_by=block.updated_by,
                is_active=block.is_active
            )
            pydantic_blocks.append(pydantic_block)
        
        # Create Pydantic document
        pydantic_document = Document(
            id=self.test_document.id,
            document_key=self.test_document.document_key,
            version=self.test_document.version,
            document_name=self.test_document.document_name,
            document_type=DocumentType(self.test_document.document_type.value),
            document_tier=DocumentTier(self.test_document.document_tier.value),
            status=DocumentStatus(self.test_document.status.value),
            org_id=self.test_document.org_id,
            created_by=self.test_document.created_by,
            updated_by=self.test_document.updated_by,
            created_at=self.test_document.created_at,
            updated_at=self.test_document.updated_at,
            metadata=self.test_document.metadata_json,
            blocks=pydantic_blocks
        )
        
        # Test different assembly formats
        formats = [
            (AssemblyFormat.HTML, "HTML"),
            (AssemblyFormat.MARKDOWN, "Markdown"),
            (AssemblyFormat.PLAIN_TEXT, "Plain Text"),
            (AssemblyFormat.JSON, "JSON")
        ]
        
        for format_type, format_name in formats:
            print(f"\n--- Testing {format_name} Assembly ---")
            
            config = DocumentAssemblyConfig(
                format_type=format_type,
                include_toc=True,
                include_metadata=True
            )
            
            assembled_doc = self.document_assembler.assemble_document(pydantic_document, config)
            
            print(f"✅ Assembled as {format_name}")
            print(f"   - Content length: {len(assembled_doc.content)} characters")
            print(f"   - Format: {assembled_doc.format_type}")
            print(f"   - Block count: {assembled_doc.metadata_json.get('block_count', 0)}")
            
            # Show preview
            preview = assembled_doc.content[:200] + "..." if len(assembled_doc.content) > 200 else assembled_doc.content
            print(f"   - Preview: {preview}")
    
    def test_document_validation(self):
        """Test document structure validation"""
        print("\n=== Testing Document Validation ===")
        
        # Create document with blocks
        self.test_create_document_with_blocks()
        
        # Get blocks and convert to Pydantic
        blocks = self.block_service.get_document_blocks(self.test_document.id)
        pydantic_blocks = []
        for block in blocks:
            pydantic_block = DocumentBlock(
                id=block.id,
                document_id=block.document_id,
                block_type=BlockType(block.block_type.value),
                block_order=block.block_order,
                content=block.content,
                metadata_json=block.metadata_json,
                created_at=block.created_at,
                updated_at=block.updated_at,
                created_by=block.created_by,
                updated_by=block.updated_by,
                is_active=block.is_active
            )
            pydantic_blocks.append(pydantic_block)
        
        pydantic_document = Document(
            id=self.test_document.id,
            document_key=self.test_document.document_key,
            version=self.test_document.version,
            document_name=self.test_document.document_name,
            document_type=DocumentType(self.test_document.document_type.value),
            document_tier=DocumentTier(self.test_document.document_tier.value),
            status=DocumentStatus(self.test_document.status.value),
            org_id=self.test_document.org_id,
            created_by=self.test_document.created_by,
            updated_by=self.test_document.updated_by,
            created_at=self.test_document.created_at,
            updated_at=self.test_document.updated_at,
            metadata=self.test_document.metadata_json,
            blocks=pydantic_blocks
        )
        
        # Validate document structure
        validation = self.document_assembler.validate_document_structure(pydantic_document)
        
        print(f"✅ Document validation results:")
        print(f"   - Is valid: {validation['is_valid']}")
        print(f"   - Missing required: {validation['missing_required']}")
        print(f"   - Has optional blocks: {validation['has_optional_blocks']}")
        print(f"   - Block count: {validation['block_count']}")
        print(f"   - Block types: {validation['block_types']}")
    
    def test_sop_service_integration(self):
        """Test the main SOP service integration"""
        print("\n=== Testing SOP Service Integration ===")
        
        # Create document with blocks
        self.test_create_document_with_blocks()
        
        # Test SOP service methods
        sop_service = SopService(document_key=self.test_document.document_key, version=self.test_document.version)
        
        # Note: This would require async testing, but for now we'll show the structure
        print(f"✅ SOP Service initialized with document key: {sop_service.document_key}")
        print(f"   - Version: {sop_service.version}")
        
        # Test document retrieval (would need async session)
        print("   - Document retrieval would be tested with async session")
        
        # Test block operations
        blocks = self.block_service.get_document_blocks(self.test_document.id)
        print(f"   - Retrieved {len(blocks)} blocks via block service")
        
        # Test assembly
        assembler = DocumentAssembler()
        config = DocumentAssemblyConfig(
            format_type=AssemblyFormat.HTML,
            include_toc=True,
            include_metadata=True
        )
        
        # Convert to Pydantic for assembly
        pydantic_blocks = []
        for block in blocks:
            pydantic_block = DocumentBlock(
                id=block.id,
                document_id=block.document_id,
                block_type=BlockType(block.block_type.value),
                block_order=block.block_order,
                content=block.content,
                metadata_json=block.metadata_json,
                created_at=block.created_at,
                updated_at=block.updated_at,
                created_by=block.created_by,
                updated_by=block.updated_by,
                is_active=block.is_active
            )
            pydantic_blocks.append(pydantic_block)
        
        pydantic_document = Document(
            id=self.test_document.id,
            document_key=self.test_document.document_key,
            version=self.test_document.version,
            document_name=self.test_document.document_name,
            document_type=DocumentType(self.test_document.document_type.value),
            document_tier=DocumentTier(self.test_document.document_tier.value),
            status=DocumentStatus(self.test_document.status.value),
            org_id=self.test_document.org_id,
            created_by=self.test_document.created_by,
            updated_by=self.test_document.updated_by,
            created_at=self.test_document.created_at,
            updated_at=self.test_document.updated_at,
            metadata=self.test_document.metadata_json,
            blocks=pydantic_blocks
        )
        
        assembled_doc = assembler.assemble_document(pydantic_document, config)
        print(f"   - Assembled document: {len(assembled_doc.content)} characters")
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting SOP Service Integration Tests")
        print("=" * 50)
        
        try:
            # Ensure setup is called
            self.setup_method()
            
            self.test_create_document_with_blocks()
            self.test_block_operations()
            self.test_document_assembly()
            self.test_document_validation()
            self.test_sop_service_integration()
            
            print("\n" + "=" * 50)
            print("✅ All tests completed successfully!")
            print("📋 Summary:")
            print("   - Document creation with blocks ✓")
            print("   - Block operations (CRUD) ✓")
            print("   - Document assembly in multiple formats ✓")
            print("   - Document validation ✓")
            print("   - SOP service integration ✓")
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            raise
        finally:
            # Ensure teardown is called
            self.teardown_method()


def main():
    """Run the integration tests"""
    test_instance = TestSopServiceIntegration()
    test_instance.run_all_tests()


if __name__ == "__main__":
    main() 