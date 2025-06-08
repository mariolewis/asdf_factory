# agent_project_bootstrap.py

"""
This module contains the ProjectBootstrapAgent class.

This agent is responsible for the initial processing of specification documents
provided by the PM for the target application. Its primary role is to extract
text content from various file formats.
(ASDF Dev Plan v0.2, F-Dev 2.2)
"""

import docx
from typing import List, Tuple

# Note: The Streamlit 'UploadedFile' object will be passed to this agent,
# so we avoid a direct 'import streamlit' to keep the agent's logic
# independent from the UI framework where possible.

class ProjectBootstrapAgent:
    """
    Processes uploaded specification documents for the target application.

    This agent extracts text from .txt, .md, and .docx files, preparing the
    content for the SpecClarificationAgent.
    (ASDF PRD v0.2, Section 3.2, Phase 1)
    """

    def __init__(self):
        """Initializes the ProjectBootstrapAgent."""
        pass

    def extract_text_from_files(self, uploaded_files: List) -> Tuple[str, List[str]]:
        """
        Extracts text content from a list of uploaded files.

        [cite_start]Supports .txt, .md, and .docx formats as per the PRD. [cite: 341]

        Args:
            uploaded_files: A list of files uploaded via st.file_uploader.

        Returns:
            A tuple containing:
            - A single string with the concatenated text from all files.
            - A list of warning or error messages encountered during processing.
        """
        all_text = []
        messages = []
        for doc in uploaded_files:
            try:
                if doc.name.endswith('.docx'):
                    # [cite_start]Use python-docx to read .docx files [cite: 343]
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

        return "\\n\\n---\\n\\n".join(all_text), messages