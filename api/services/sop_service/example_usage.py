# api/services/sop_service/example_usage.py
# Example usage of the new flexible block-based document system

from typing import List, Dict, Any
from datetime import datetime

from .models.models import (
    Document, DocumentBlock, BlockType, DocumentType, DocumentTier, DocumentStatus,
    StepBlockContent, QuestionBlockContent, ImageBlockContent, ChecklistBlockContent,
    DocumentAssemblyConfig, AssemblyFormat
)
from .block_service import BlockService
from .document_assembly import DocumentAssembler


def create_sample_sop_document() -> Document:
    """Create a sample SOP document using the new block-based system"""
    
    # Create the main document
    document = Document(
        id=1,
        document_key=1001,
        version=1,
        document_name="Laboratory Safety Procedures",
        document_type=DocumentType.SOP,
        document_tier=DocumentTier.PRO,
        status=DocumentStatus.DRAFT,
        org_id=1,
        created_by=1,
        updated_by=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        metadata={
            "department": "Laboratory",
            "risk_level": "medium",
            "review_frequency": "annual"
        }
    )
    
    # Create blocks for the document
    blocks = [
        # Title block
        DocumentBlock(
            id=1,
            document_id=1,
            block_type=BlockType.TITLE,
            block_order=1,
            content={"text": "Laboratory Safety Procedures"},
            created_by=1,
            updated_by=1
        ),
        
        # Description block
        DocumentBlock(
            id=2,
            document_id=1,
            block_type=BlockType.DESCRIPTION,
            block_order=2,
            content={"text": "This document outlines the safety procedures that must be followed when working in the laboratory."},
            created_by=1,
            updated_by=1
        ),
        
        # PPE Required block
        DocumentBlock(
            id=3,
            document_id=1,
            block_type=BlockType.PPE_REQUIRED,
            block_order=3,
            content={"text": "Safety goggles, lab coat, and closed-toe shoes must be worn at all times."},
            created_by=1,
            updated_by=1
        ),
        
        # Warning block
        DocumentBlock(
            id=4,
            document_id=1,
            block_type=BlockType.WARNING,
            block_order=4,
            content={"text": "Failure to follow these procedures may result in serious injury or death."},
            created_by=1,
            updated_by=1
        ),
        
        # Section header
        DocumentBlock(
            id=5,
            document_id=1,
            block_type=BlockType.SECTION_HEADER,
            block_order=5,
            content={"text": "Pre-Entry Procedures"},
            created_by=1,
            updated_by=1
        ),
        
        # Step blocks
        DocumentBlock(
            id=6,
            document_id=1,
            block_type=BlockType.STEP,
            block_order=6,
            content={
                "step_number": 1,
                "step_description": "Check safety equipment",
                "step_instructions": "Ensure all safety equipment is available and in good condition before entering the laboratory.",
                "step_expected_result": "All safety equipment is verified and ready for use.",
                "step_who_responsible": "Laboratory technician",
                "ppe_required": True
            },
            created_by=1,
            updated_by=1
        ),
        
        DocumentBlock(
            id=7,
            document_id=1,
            block_type=BlockType.STEP,
            block_order=7,
            content={
                "step_number": 2,
                "step_description": "Review hazard assessment",
                "step_instructions": "Review the hazard assessment for any experiments or procedures planned for the day.",
                "step_expected_result": "All hazards are identified and understood.",
                "step_who_responsible": "Laboratory supervisor",
                "ppe_required": False
            },
            created_by=1,
            updated_by=1
        ),
        
        # Section header
        DocumentBlock(
            id=8,
            document_id=1,
            block_type=BlockType.SECTION_HEADER,
            block_order=8,
            content={"text": "During Laboratory Work"},
            created_by=1,
            updated_by=1
        ),
        
        # More step blocks
        DocumentBlock(
            id=9,
            document_id=1,
            block_type=BlockType.STEP,
            block_order=9,
            content={
                "step_number": 3,
                "step_description": "Maintain clean workspace",
                "step_instructions": "Keep your workspace clean and organized. Dispose of waste materials properly.",
                "step_expected_result": "Workspace remains clean and safe throughout the day.",
                "step_who_responsible": "All laboratory personnel",
                "ppe_required": True
            },
            created_by=1,
            updated_by=1
        ),
        
        # Question block
        DocumentBlock(
            id=10,
            document_id=1,
            block_type=BlockType.QUESTION,
            block_order=10,
            content={
                "question": "What should you do if you encounter an unknown chemical?",
                "status": "answered",
                "answer": "Stop work immediately, isolate the area, and contact the laboratory supervisor.",
                "answered_by": 1,
                "answered_at": datetime.now().isoformat()
            },
            created_by=1,
            updated_by=1
        ),
        
        # Additional info block
        DocumentBlock(
            id=11,
            document_id=1,
            block_type=BlockType.ADDITIONAL_INFO,
            block_order=11,
            content={"text": "For additional safety information, refer to the Laboratory Safety Manual or contact the Safety Officer."},
            created_by=1,
            updated_by=1
        )
    ]
    
    document.blocks = blocks
    return document


def demonstrate_block_operations():
    """Demonstrate various block operations"""
    
    # This would typically be done with a real database session
    # For this example, we'll show the concepts
    
    print("=== Block-Based Document System Example ===\n")
    
    # Create a sample document
    document = create_sample_sop_document()
    print(f"Created document: {document.document_name}")
    print(f"Document type: {document.document_type.value}")
    print(f"Number of blocks: {len(document.blocks)}")
    print(f"Block types: {[block.block_type.value for block in document.blocks]}\n")
    
    # Demonstrate block operations (conceptual)
    print("=== Block Operations ===\n")
    
    # 1. Adding a new step block
    new_step_content = StepBlockContent(
        content="New step content",
        step_number=4,
        step_description="Emergency procedures",
        step_instructions="In case of emergency, follow the emergency evacuation procedures.",
        step_expected_result="All personnel safely evacuated.",
        step_who_responsible="All laboratory personnel",
        ppe_required=True
    )
    print("1. Adding new step block:")
    print(f"   - Step: {new_step_content.step_description}")
    print(f"   - PPE Required: {new_step_content.ppe_required}\n")
    
    # 2. Adding a question block
    new_question_content = QuestionBlockContent(
        content="Question content",
        question="What is the emergency contact number?",
        status="open"
    )
    print("2. Adding new question block:")
    print(f"   - Question: {new_question_content.question}")
    print(f"   - Status: {new_question_content.status.value}\n")
    
    # 3. Adding an image block
    new_image_content = ImageBlockContent(
        content="Image content",
        image_url="/images/safety-equipment.jpg",
        alt_text="Safety equipment layout",
        caption="Proper arrangement of safety equipment in the laboratory"
    )
    print("3. Adding new image block:")
    print(f"   - Image: {new_image_content.image_url}")
    print(f"   - Caption: {new_image_content.caption}\n")
    
    # 4. Adding a checklist block
    new_checklist_content = ChecklistBlockContent(
        content="Checklist content",
        items=[
            {"id": 1, "text": "Safety goggles", "checked": False},
            {"id": 2, "text": "Lab coat", "checked": False},
            {"id": 3, "text": "Closed-toe shoes", "checked": False},
            {"id": 4, "text": "Gloves", "checked": False}
        ],
        allow_multiple=False
    )
    print("4. Adding new checklist block:")
    print(f"   - Items: {len(new_checklist_content.items)}")
    print(f"   - Allow multiple: {new_checklist_content.allow_multiple}\n")


def demonstrate_document_assembly():
    """Demonstrate document assembly capabilities"""
    
    print("=== Document Assembly ===\n")
    
    # Create sample document
    document = create_sample_sop_document()
    
    # Create assembler
    assembler = DocumentAssembler()
    
    # Assembly configurations
    configs = [
        DocumentAssemblyConfig(
            format_type=AssemblyFormat.HTML,
            include_toc=True,
            include_metadata=True
        ),
        DocumentAssemblyConfig(
            format_type=AssemblyFormat.MARKDOWN,
            include_toc=True,
            include_metadata=False
        ),
        DocumentAssemblyConfig(
            format_type=AssemblyFormat.PLAIN_TEXT,
            include_toc=False,
            include_metadata=False
        )
    ]
    
    # Assemble documents in different formats
    for i, config in enumerate(configs, 1):
        print(f"{i}. Assembling as {config.format_type.upper()}:")
        
        assembled_doc = assembler.assemble_document(document, config)
        
        print(f"   - Format: {assembled_doc.format_type}")
        print(f"   - Content length: {len(assembled_doc.content)} characters")
        print(f"   - Block count: {assembled_doc.metadata.get('block_count', 0)}")
        
        # Show a preview of the content
        preview = assembled_doc.content[:200] + "..." if len(assembled_doc.content) > 200 else assembled_doc.content
        print(f"   - Preview: {preview}\n")
    
    # Validate document structure
    print("5. Document Structure Validation:")
    validation = assembler.validate_document_structure(document)
    print(f"   - Is valid: {validation['is_valid']}")
    print(f"   - Missing required: {validation['missing_required']}")
    print(f"   - Has optional blocks: {validation['has_optional_blocks']}")
    print(f"   - Block count: {validation['block_count']}")
    print(f"   - Block types: {validation['block_types']}\n")


def demonstrate_different_document_types():
    """Demonstrate how the same system can handle different document types"""
    
    print("=== Different Document Types ===\n")
    
    # 1. SOP Document
    sop_document = Document(
        id=1,
        document_key=1001,
        version=1,
        document_name="Chemical Handling SOP",
        document_type=DocumentType.SOP,
        document_tier=DocumentTier.ENTERPRISE,
        status=DocumentStatus.PUBLISHED,
        org_id=1,
        created_by=1,
        updated_by=1
    )
    
    # 2. Procedure Document
    procedure_document = Document(
        id=2,
        document_key=1002,
        version=1,
        document_name="Equipment Calibration Procedure",
        document_type=DocumentType.PROCEDURE,
        document_tier=DocumentTier.PRO,
        status=DocumentStatus.APPROVED,
        org_id=1,
        created_by=1,
        updated_by=1
    )
    
    # 3. Checklist Document
    checklist_document = Document(
        id=3,
        document_key=1003,
        version=1,
        document_name="Daily Safety Checklist",
        document_type=DocumentType.CHECKLIST,
        document_tier=DocumentType.FREE,
        status=DocumentStatus.PUBLISHED,
        org_id=1,
        created_by=1,
        updated_by=1
    )
    
    # 4. Policy Document
    policy_document = Document(
        id=4,
        document_key=1004,
        version=1,
        document_name="Data Security Policy",
        document_type=DocumentType.POLICY,
        document_tier=DocumentTier.ENTERPRISE,
        status=DocumentStatus.PUBLISHED,
        org_id=1,
        created_by=1,
        updated_by=1
    )
    
    documents = [sop_document, procedure_document, checklist_document, policy_document]
    
    for doc in documents:
        print(f"Document: {doc.document_name}")
        print(f"  - Type: {doc.document_type.value}")
        print(f"  - Tier: {doc.document_tier.value}")
        print(f"  - Status: {doc.status.value}")
        print(f"  - Can use same block system: Yes")
        print(f"  - Flexible content structure: Yes\n")


def demonstrate_tier_capabilities():
    """Demonstrate how different tiers can have different capabilities"""
    
    print("=== Tier Capabilities ===\n")
    
    tiers = [
        (DocumentTier.FREE, "Basic features"),
        (DocumentTier.PRO, "Advanced features"),
        (DocumentTier.ENTERPRISE, "Full features"),
        (DocumentTier.CUSTOM, "Custom features")
    ]
    
    for tier, description in tiers:
        print(f"{tier.value.upper()} Tier:")
        print(f"  - {description}")
        
        if tier == DocumentTier.FREE:
            print("  - Basic block types only")
            print("  - Limited document types")
            print("  - Basic assembly formats")
        elif tier == DocumentTier.PRO:
            print("  - All block types")
            print("  - All document types")
            print("  - Advanced assembly formats")
            print("  - Document validation")
        elif tier == DocumentTier.ENTERPRISE:
            print("  - All block types")
            print("  - All document types")
            print("  - All assembly formats")
            print("  - Advanced validation")
            print("  - Custom templates")
            print("  - Workflow integration")
        elif tier == DocumentTier.CUSTOM:
            print("  - Custom block types")
            print("  - Custom document types")
            print("  - Custom assembly formats")
            print("  - Custom validation rules")
            print("  - Full customization")
        
        print()


if __name__ == "__main__":
    """Run the demonstration"""
    
    demonstrate_block_operations()
    demonstrate_document_assembly()
    demonstrate_different_document_types()
    demonstrate_tier_capabilities()
    
    print("=== Summary ===")
    print("The new block-based system provides:")
    print("✅ Flexible document structure")
    print("✅ Support for multiple document types")
    print("✅ Tier-based feature access")
    print("✅ Easy content management")
    print("✅ Multiple output formats")
    print("✅ Backward compatibility")
    print("✅ Extensible architecture") 