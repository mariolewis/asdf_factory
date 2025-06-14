# agent_project_bootstrap.py

"""
This module contains the ProjectBootstrapAgent class.

This agent is responsible for the initial processing of specification documents
provided by the PM for the target application. Its primary role is to extract
text content from various file formats and enforce initial project size limits.
(ASDF Dev Plan v0.4, F-Dev 2.2)
"""

import docx
from typing import List, Tuple, Optional

# Note: The Streamlit 'UploadedFile' object will be passed to this agent,
# so we avoid a direct 'import streamlit' to keep the agent's logic
# independent from the UI framework where possible.

# A configurable limit to prevent overly large specifications from being processed.
# (ASDF Change Request CR-ASDF-004, Stage 1: Dynamic Size Guardrail)
# For this implementation, we use a fixed but easily configurable value.
# A future enhancement could make this truly dynamic based on the LLM's token limit.
SPEC_MAX_CHAR_LIMIT = 30000


class ProjectBootstrapAgent:
    """
    Processes uploaded specification documents for the target application.

    This agent extracts text from .txt, .md, and .docx files, preparing the
    content for the SpecClarificationAgent. It also enforces a size limit
    on the incoming specification.
    (ASDF PRD v0.4, Section 3.2, Phase 1)
    """

    def __init__(self):
        """Initializes the ProjectBootstrapAgent."""
        pass

    def extract_text_from_files(self, uploaded_files: List) -> Tuple[Optional[str], List[str], Optional[str]]:
        """
        Extracts text content from a list of uploaded files and checks size limits.

        Supports .txt, .md, and .docx formats as per the PRD.
        Implements the size guardrail from CR-ASDF-004.

        Args:
            uploaded_files: A list of files uploaded via st.file_uploader.

        Returns:
            A tuple containing:
            - A single string with the concatenated text from all files, or None on error.
            - A list of warning messages encountered during processing.
            - An error string if a fatal error occurs (like spec too large), otherwise None.
        """
        all_text = []
        messages = []
        for doc in uploaded_files:
            try:
                if doc.name.endswith('.docx'):
                    # Use python-docx to read .docx files
                    document = docx.Document(doc)
                    for para in document.paragraphs:
                        all_text.append(para.text)
                elif doc.name.endswith(('.txt', '.md')):
                    # Read .txt and .md files as plain text
                    all_text.append(doc.getvalue().decode("utf-8"))
                else:
                    # Handle unsupported file types gracefully
                    messages.append(f"Warning: Unsupported file type '{doc.name}' was skipped.")
            except Exception as e:
                messages.append(f"Error: Could not process file '{doc.name}'. Reason: {e}")

        concatenated_text = "\n\n---\n\n".join(all_text)

        # (CR-ASDF-004) Stage 1: Dynamic Size Guardrail Implementation
        if len(concatenated_text) > SPEC_MAX_CHAR_LIMIT:
            error_message = (
                "The provided specification is too large for a single project. "
                "Please divide it into smaller, more focused sub-projects."
            )
            messages.append(f"Error: Specification character count ({len(concatenated_text)}) exceeds the limit of {SPEC_MAX_CHAR_LIMIT}.")
            return None, messages, error_message

        return concatenated_text, messages, None