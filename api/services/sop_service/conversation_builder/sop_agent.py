from __future__ import annotations

SYSTEM_PROMPT = (
    "You are a helpful SOP drafting assistant."
    " Ask at most one clarifying question per turn."
    " Never fabricate facts."
    " Be concise and use plain language."
    " Maintain short-term memory; do not repeat questions that were answered."
)

WHITELISTED_TOOLS = {
    "create_or_get_document",
    "add_or_update_title",
    "add_or_update_description",
    "add_or_update_step",
    "insert_step_before",
    "delete_step",
    "add_question",
    "answer_question",
    "add_safety_block",
    "get_document_blocks",
    "assemble_document",
    "write_mermaid_from_trace",
}


