# agent_project_bootstrap.py

"""
This module contains the ProjectBootstrapAgent class.

This agent is responsible for the initial processing of specification documents
provided by the PM for the target application. Its primary role is to extract
text content from various file formats and enforce initial project size limits.
(ASDF Dev Plan v0.4, F-Dev 2.2)
"""

import docx
import logging
from typing import List, Tuple, Optional
from asdf_db_manager import ASDFDBManager
from pypdf import PdfReader

# Note: The Streamlit 'UploadedFile' object will be passed to this agent,
# so we avoid a direct 'import streamlit' to keep the agent's logic
# independent from the UI framework where possible.

class ProjectBootstrapAgent:
    """
    Processes uploaded specification documents for the target application.

    This agent extracts text from .txt, .md, .docx, and .pdf files, preparing the
    content for the SpecClarificationAgent. It enforces a dynamic size limit
    on the incoming specification based on the active factory configuration.
    """

    def __init__(self, db_manager: ASDFDBManager):
        """
        Initializes the ProjectBootstrapAgent.

        Args:
            db_manager (ASDFDBManager): An instance of the database manager to access config.
        """
        if not db_manager:
            raise ValueError("db_manager is required for the ProjectBootstrapAgent.")
        self.db_manager = db_manager


    def extract_text_from_files(self, uploaded_files: List) -> Tuple[Optional[str], List[str], Optional[str]]:
        """
        Extracts text content from a list of uploaded files and checks size limits.

        Supports .txt, .md, .docx, and .pdf formats.
        Implements the dynamic size guardrail by reading the active context limit from the database.

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
                elif doc.name.endswith('.pdf'):
                    # Use pypdf to read .pdf files
                    try:
                        pdf_reader = PdfReader(doc)
                        for page in pdf_reader.pages:
                            all_text.append(page.extract_text() or "")
                    except Exception as pdf_e:
                        messages.append(f"Warning: Could not read PDF file '{doc.name}'. It may be corrupted or image-based. Error: {pdf_e}")
                elif doc.name.endswith(('.txt', '.md')):
                    # Read .txt and .md files as plain text
                    all_text.append(doc.getvalue().decode("utf-8"))
                else:
                    # Handle unsupported file types gracefully
                    messages.append(f"Warning: Unsupported file type '{doc.name}' was skipped.")
            except Exception as e:
                messages.append(f"Error: Could not process file '{doc.name}'. Reason: {e}")

        concatenated_text = "\n\n---\n\n".join(all_text)

        try:
            with self.db_manager as db:
                limit_str = db.get_config_value("CONTEXT_WINDOW_CHAR_LIMIT") or "2000000"
            spec_max_char_limit = int(limit_str)
        except Exception as e:
            logging.error(f"Could not read CONTEXT_WINDOW_CHAR_LIMIT from DB, using default. Error: {e}")
            spec_max_char_limit = 128000 # Fallback to the most restrictive default

        if len(concatenated_text) > spec_max_char_limit:
            error_message = (
                "The provided specification is too large for a single project based on the current LLM's context limit. "
                "Please divide it into smaller, more focused sub-projects or select an LLM with a larger context window in Settings."
            )
            messages.append(f"Error: Specification character count ({len(concatenated_text):,}) exceeds the active limit of {spec_max_char_limit:,}.")
            return None, messages, error_message

        return concatenated_text, messages, None