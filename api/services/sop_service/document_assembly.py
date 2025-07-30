# api/services/sop_service/document_assembly.py
# Document assembly service for converting blocks to structured documents

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json
import re

from .models.models import (
    Document, DocumentBlock, BlockType, DocumentAssemblyConfig, 
    AssembledDocument, DocumentType, DocumentTier
)


class AssemblyFormat(str, Enum):
    HTML = "html"
    MARKDOWN = "markdown"
    PDF = "pdf"
    PLAIN_TEXT = "plain_text"
    JSON = "json"


class DocumentAssembler:
    """Service for assembling documents from blocks into structured formats"""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def assemble_document(
        self, 
        document: Document, 
        config: DocumentAssemblyConfig
    ) -> AssembledDocument:
        """
        Assemble a document from its blocks into a structured format
        
        Args:
            document: The document to assemble
            config: Assembly configuration
            
        Returns:
            AssembledDocument with the structured content
        """
        # Sort blocks by order
        sorted_blocks = sorted(document.blocks, key=lambda b: b.block_order)
        
        # Generate content based on format
        if config.format_type == AssemblyFormat.HTML:
            content = self._assemble_html(document, sorted_blocks, config)
        elif config.format_type == AssemblyFormat.MARKDOWN:
            content = self._assemble_markdown(document, sorted_blocks, config)
        elif config.format_type == AssemblyFormat.PLAIN_TEXT:
            content = self._assemble_plain_text(document, sorted_blocks, config)
        elif config.format_type == AssemblyFormat.JSON:
            content = self._assemble_json(document, sorted_blocks, config)
        else:
            raise ValueError(f"Unsupported format: {config.format_type}")
        
        return AssembledDocument(
            document_id=document.id,
            content=content,
            format_type=config.format_type,
            metadata={
                "document_type": document.document_type.value,
                "document_tier": document.document_tier.value,
                "assembly_config": config.model_dump(),
                "block_count": len(sorted_blocks)
            }
        )
    
    def _assemble_html(self, document: Document, blocks: List[DocumentBlock], config: DocumentAssemblyConfig) -> str:
        """Assemble document as HTML"""
        html_parts = []
        
        # Document header
        html_parts.append(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{document.document_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .document-header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
                .document-title {{ font-size: 2em; font-weight: bold; color: #333; }}
                .document-meta {{ color: #666; margin-top: 10px; }}
                .block {{ margin-bottom: 20px; }}
                .step {{ border-left: 4px solid #007bff; padding-left: 15px; margin: 15px 0; }}
                .question {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; }}
                .caution {{ background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; }}
                .ppe-required {{ background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 5px; }}
                .toc {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
        """)
        
        # Document header
        html_parts.append(f"""
        <div class="document-header">
            <div class="document-title">{document.document_name}</div>
            <div class="document-meta">
                <strong>Type:</strong> {document.document_type.value.title()} | 
                <strong>Version:</strong> {document.version} | 
                <strong>Status:</strong> {document.status.value.title()} |
                <strong>Created:</strong> {document.created_at.strftime('%Y-%m-%d')}
            </div>
        </div>
        """)
        
        # Table of contents if requested
        if config.include_toc:
            toc_blocks = [b for b in blocks if b.block_type in [BlockType.SECTION_HEADER, BlockType.STEP]]
            if toc_blocks:
                html_parts.append('<div class="toc"><h2>Table of Contents</h2><ul>')
                for block in toc_blocks:
                    if block.block_type == BlockType.SECTION_HEADER:
                        content = block.content.get('text', '') if isinstance(block.content, dict) else str(block.content)
                        html_parts.append(f'<li><a href="#section-{block.id}">{content}</a></li>')
                    elif block.block_type == BlockType.STEP:
                        step_num = block.content.get('step_number', '') if isinstance(block.content, dict) else ''
                        step_desc = block.content.get('step_description', '') if isinstance(block.content, dict) else ''
                        html_parts.append(f'<li><a href="#step-{block.id}">Step {step_num}: {step_desc}</a></li>')
                html_parts.append('</ul></div>')
        
        # Process blocks
        for block in blocks:
            html_parts.append(self._render_block_html(block))
        
        # Document footer
        if config.include_metadata and document.metadata_json:
            html_parts.append(f"""
            <div class="document-footer" style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd;">
                <h3>Document Metadata</h3>
                <pre>{json.dumps(document.metadata_json, indent=2)}</pre>
            </div>
            """)
        
        html_parts.append("</body></html>")
        
        return "\n".join(html_parts)
    
    def _render_block_html(self, block: DocumentBlock) -> str:
        """Render a single block as HTML"""
        content = block.content if isinstance(block.content, dict) else {"text": str(block.content)}
        
        if block.block_type == BlockType.TITLE:
            return f'<h1 id="title">{content.get("text", "")}</h1>'
        
        elif block.block_type == BlockType.DESCRIPTION:
            return f'<div class="block"><p>{content.get("text", "")}</p></div>'
        
        elif block.block_type == BlockType.SECTION_HEADER:
            return f'<h2 id="section-{block.id}" class="block">{content.get("text", "")}</h2>'
        
        elif block.block_type == BlockType.STEP:
            step_num = content.get("step_number", "")
            step_desc = content.get("step_description", "")
            step_instructions = content.get("step_instructions", "")
            step_result = content.get("step_expected_result", "")
            step_responsible = content.get("step_who_responsible", "")
            ppe_required = content.get("ppe_required", False)
            
            html = f'<div id="step-{block.id}" class="step">'
            html += f'<h3>Step {step_num}: {step_desc}</h3>'
            html += f'<p><strong>Instructions:</strong> {step_instructions}</p>'
            
            if step_result:
                html += f'<p><strong>Expected Result:</strong> {step_result}</p>'
            
            if step_responsible:
                html += f'<p><strong>Responsible:</strong> {step_responsible}</p>'
            
            if ppe_required:
                html += '<div class="ppe-required"><strong>⚠️ PPE Required</strong></div>'
            
            html += '</div>'
            return html
        
        elif block.block_type == BlockType.QUESTION:
            question = content.get("question", "")
            answer = content.get("answer", "")
            status = content.get("status", "open")
            
            html = f'<div class="question">'
            html += f'<h4>Question: {question}</h4>'
            if answer:
                html += f'<p><strong>Answer:</strong> {answer}</p>'
            html += f'<p><em>Status: {status}</em></p>'
            html += '</div>'
            return html
        
        elif block.block_type == BlockType.WARNING:
            return f'<div class="warning"><strong>⚠️ WARNING:</strong> {content.get("text", "")}</div>'
        
        elif block.block_type == BlockType.CAUTION:
            return f'<div class="caution"><strong>⚠️ CAUTION:</strong> {content.get("text", "")}</div>'
        
        elif block.block_type == BlockType.PPE_REQUIRED:
            return f'<div class="ppe-required"><strong>🛡️ PPE Required:</strong> {content.get("text", "")}</div>'
        
        elif block.block_type == BlockType.ADDITIONAL_INFO:
            return f'<div class="block"><h3>Additional Information</h3><p>{content.get("text", "")}</p></div>'
        
        else:
            # Generic block rendering
            return f'<div class="block"><p>{content.get("text", str(content))}</p></div>'
    
    def _assemble_markdown(self, document: Document, blocks: List[DocumentBlock], config: DocumentAssemblyConfig) -> str:
        """Assemble document as Markdown"""
        md_parts = []
        
        # Document header
        md_parts.append(f"# {document.document_name}\n")
        md_parts.append(f"**Type:** {document.document_type.value.title()} | **Version:** {document.version} | **Status:** {document.status.value.title()}\n")
        md_parts.append(f"**Created:** {document.created_at.strftime('%Y-%m-%d')}\n\n")
        
        # Table of contents
        if config.include_toc:
            md_parts.append("## Table of Contents\n")
            for block in blocks:
                if block.block_type == BlockType.SECTION_HEADER:
                    content = block.content.get('text', '') if isinstance(block.content, dict) else str(block.content)
                    md_parts.append(f"- {content}\n")
                elif block.block_type == BlockType.STEP:
                    step_num = block.content.get('step_number', '') if isinstance(block.content, dict) else ''
                    step_desc = block.content.get('step_description', '') if isinstance(block.content, dict) else ''
                    md_parts.append(f"- Step {step_num}: {step_desc}\n")
            md_parts.append("\n---\n\n")
        
        # Process blocks
        for block in blocks:
            md_parts.append(self._render_block_markdown(block))
        
        # Metadata
        if config.include_metadata and document.metadata_json:
            md_parts.append("\n## Document Metadata\n")
            md_parts.append(f"```json\n{json.dumps(document.metadata_json, indent=2)}\n```\n")
        
        return "".join(md_parts)
    
    def _render_block_markdown(self, block: DocumentBlock) -> str:
        """Render a single block as Markdown"""
        content = block.content if isinstance(block.content, dict) else {"text": str(block.content)}
        
        if block.block_type == BlockType.TITLE:
            return f"# {content.get('text', '')}\n\n"
        
        elif block.block_type == BlockType.DESCRIPTION:
            return f"{content.get('text', '')}\n\n"
        
        elif block.block_type == BlockType.SECTION_HEADER:
            return f"## {content.get('text', '')}\n\n"
        
        elif block.block_type == BlockType.STEP:
            step_num = content.get("step_number", "")
            step_desc = content.get("step_description", "")
            step_instructions = content.get("step_instructions", "")
            step_result = content.get("step_expected_result", "")
            step_responsible = content.get("step_who_responsible", "")
            ppe_required = content.get("ppe_required", False)
            
            md = f"### Step {step_num}: {step_desc}\n\n"
            md += f"**Instructions:** {step_instructions}\n\n"
            
            if step_result:
                md += f"**Expected Result:** {step_result}\n\n"
            
            if step_responsible:
                md += f"**Responsible:** {step_responsible}\n\n"
            
            if ppe_required:
                md += "⚠️ **PPE Required**\n\n"
            
            return md
        
        elif block.block_type == BlockType.QUESTION:
            question = content.get("question", "")
            answer = content.get("answer", "")
            status = content.get("status", "open")
            
            md = f"#### Question: {question}\n\n"
            if answer:
                md += f"**Answer:** {answer}\n\n"
            md += f"*Status: {status}*\n\n"
            return md
        
        elif block.block_type == BlockType.WARNING:
            return f"⚠️ **WARNING:** {content.get('text', '')}\n\n"
        
        elif block.block_type == BlockType.CAUTION:
            return f"⚠️ **CAUTION:** {content.get('text', '')}\n\n"
        
        elif block.block_type == BlockType.PPE_REQUIRED:
            return f"🛡️ **PPE Required:** {content.get('text', '')}\n\n"
        
        elif block.block_type == BlockType.ADDITIONAL_INFO:
            return f"### Additional Information\n\n{content.get('text', '')}\n\n"
        
        else:
            return f"{content.get('text', str(content))}\n\n"
    
    def _assemble_plain_text(self, document: Document, blocks: List[DocumentBlock], config: DocumentAssemblyConfig) -> str:
        """Assemble document as plain text"""
        text_parts = []
        
        # Document header
        text_parts.append(f"{document.document_name}")
        text_parts.append("=" * len(document.document_name))
        text_parts.append(f"Type: {document.document_type.value.title()}")
        text_parts.append(f"Version: {document.version}")
        text_parts.append(f"Status: {document.status.value.title()}")
        text_parts.append(f"Created: {document.created_at.strftime('%Y-%m-%d')}")
        text_parts.append("")
        
        # Process blocks
        for block in blocks:
            text_parts.append(self._render_block_plain_text(block))
        
        return "\n".join(text_parts)
    
    def _render_block_plain_text(self, block: DocumentBlock) -> str:
        """Render a single block as plain text"""
        content = block.content if isinstance(block.content, dict) else {"text": str(block.content)}
        
        if block.block_type == BlockType.TITLE:
            return f"{content.get('text', '')}\n"
        
        elif block.block_type == BlockType.DESCRIPTION:
            return f"{content.get('text', '')}\n"
        
        elif block.block_type == BlockType.SECTION_HEADER:
            return f"\n{content.get('text', '')}\n{'-' * len(content.get('text', ''))}\n"
        
        elif block.block_type == BlockType.STEP:
            step_num = content.get("step_number", "")
            step_desc = content.get("step_description", "")
            step_instructions = content.get("step_instructions", "")
            step_result = content.get("step_expected_result", "")
            step_responsible = content.get("step_who_responsible", "")
            ppe_required = content.get("ppe_required", False)
            
            text = f"Step {step_num}: {step_desc}\n"
            text += f"Instructions: {step_instructions}\n"
            
            if step_result:
                text += f"Expected Result: {step_result}\n"
            
            if step_responsible:
                text += f"Responsible: {step_responsible}\n"
            
            if ppe_required:
                text += "PPE Required\n"
            
            text += "\n"
            return text
        
        elif block.block_type == BlockType.QUESTION:
            question = content.get("question", "")
            answer = content.get("answer", "")
            status = content.get("status", "open")
            
            text = f"Question: {question}\n"
            if answer:
                text += f"Answer: {answer}\n"
            text += f"Status: {status}\n\n"
            return text
        
        elif block.block_type == BlockType.WARNING:
            return f"WARNING: {content.get('text', '')}\n"
        
        elif block.block_type == BlockType.CAUTION:
            return f"CAUTION: {content.get('text', '')}\n"
        
        elif block.block_type == BlockType.PPE_REQUIRED:
            return f"PPE Required: {content.get('text', '')}\n"
        
        else:
            return f"{content.get('text', str(content))}\n"
    
    def _assemble_json(self, document: Document, blocks: List[DocumentBlock], config: DocumentAssemblyConfig) -> str:
        """Assemble document as JSON"""
        assembled_doc = {
            "document": {
                "id": document.id,
                "document_key": document.document_key,
                "version": document.version,
                "document_name": document.document_name,
                "document_type": document.document_type.value,
                "document_tier": document.document_tier.value,
                "status": document.status.value,
                "created_at": document.created_at.isoformat(),
                "updated_at": document.updated_at.isoformat(),
                "metadata": document.metadata_json
            },
            "blocks": [
                {
                                    "id": block.id,
                "block_type": block.block_type.value,
                "block_order": block.block_order,
                "content": block.content,
                "metadata": block.metadata_json,
                "created_at": block.created_at.isoformat(),
                "updated_at": block.updated_at.isoformat()
                }
                for block in blocks
            ]
        }
        
        return json.dumps(assembled_doc, indent=2)
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load document templates for different types"""
        return {
            "sop": {
                "required_blocks": [BlockType.TITLE, BlockType.DESCRIPTION],
                "optional_blocks": [BlockType.STEP, BlockType.PPE_REQUIRED, BlockType.WARNING, BlockType.CAUTION]
            },
            "procedure": {
                "required_blocks": [BlockType.TITLE, BlockType.DESCRIPTION, BlockType.STEP],
                "optional_blocks": [BlockType.PPE_REQUIRED, BlockType.WARNING, BlockType.CAUTION]
            },
            "checklist": {
                "required_blocks": [BlockType.TITLE, BlockType.CHECKLIST],
                "optional_blocks": [BlockType.DESCRIPTION, BlockType.PPE_REQUIRED]
            }
        }
    
    def validate_document_structure(self, document: Document) -> Dict[str, Any]:
        """Validate that a document has the required blocks for its type"""
        template = self.templates.get(document.document_type.value, {})
        required_blocks = template.get("required_blocks", [])
        optional_blocks = template.get("optional_blocks", [])
        
        block_types = [block.block_type for block in document.blocks]
        
        missing_required = [bt for bt in required_blocks if bt not in block_types]
        has_optional = any(bt in block_types for bt in optional_blocks)
        
        return {
            "is_valid": len(missing_required) == 0,
            "missing_required": missing_required,
            "has_optional_blocks": has_optional,
            "block_count": len(document.blocks),
            "block_types": list(set(block_types))
        } 