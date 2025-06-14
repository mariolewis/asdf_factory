# agents/agent_report_generator.py

"""
This module contains the ReportGeneratorAgent class.
This agent is responsible for generating formatted .docx reports.
"""

import logging
from docx import Document
from docx.shared import Inches
from io import BytesIO
import json
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

class ReportGeneratorAgent:
    """
    Agent responsible for generating downloadable .docx files for various
    project reports.
    """

    def __init__(self):
        """Initializes the ReportGeneratorAgent."""
        logging.info("ReportGeneratorAgent initialized.")

    def generate_progress_summary_docx(self, total_components: int, status_counts: dict) -> BytesIO:
        """
        Generates a .docx file for the Development Progress Summary report.

        Args:
            total_components (int): The total number of components in the plan.
            status_counts (dict): A dictionary mapping status to count.

        Returns:
            BytesIO: An in-memory byte stream of the generated .docx file.
        """
        document = Document()
        document.add_heading('ASDF - Development Progress Summary', level=1)

        document.add_paragraph(f"Total Components Defined in Plan: {total_components}")

        document.add_heading('Components by Status', level=2)
        if status_counts:
            for status, count in status_counts.items():
                document.add_paragraph(f"{status}: {count}", style='List Bullet')
        else:
            document.add_paragraph("No components with status available.")

        # Save document to an in-memory buffer
        doc_buffer = BytesIO()
        document.save(doc_buffer)
        doc_buffer.seek(0)
        return doc_buffer

    def generate_cr_bug_report_docx(self, report_data: list, filter_type: str) -> BytesIO:
        """
        Generates a .docx file for the Change Requests & Bug Fixes report.

        Args:
            report_data (list): A list of dictionaries, where each dict is a CR or Bug.
            filter_type (str): The filter applied to the report (e.g., "Pending", "All").

        Returns:
            BytesIO: An in-memory byte stream of the generated .docx file.
        """
        document = Document()
        document.add_heading('ASDF - Change Requests & Bug Fixes', level=1)
        document.add_paragraph(f"Report Filter: {filter_type}")

        if not report_data:
            document.add_paragraph("No items match the selected filter.")
        else:
            # Define table headers
            headers = ["ID", "Type", "Status", "Description"]
            table = document.add_table(rows=1, cols=len(headers))
            table.style = 'Table Grid'
            hdr_cells = table.rows[0].cells
            for i, header_name in enumerate(headers):
                hdr_cells[i].text = header_name

            # Populate table with data
            for item in report_data:
                row_cells = table.add_row().cells
                row_cells[0].text = str(item.get("id", "N/A"))
                row_cells[1].text = item.get("type", "N/A")
                row_cells[2].text = item.get("status", "N/A")
                row_cells[3].text = item.get("description", "N/A")

        # Save document to an in-memory buffer
        doc_buffer = BytesIO()
        document.save(doc_buffer)
        doc_buffer.seek(0)
        return doc_buffer

    def generate_text_document_docx(self, title: str, content: str, is_code: bool = False) -> BytesIO:
        """
        Generates a generic .docx file for text-based project documents.

        Args:
            title (str): The title of the document.
            content (str): The full text content of the document.
            is_code (bool, optional): If True, formats content in a monospaced font.
                                      Defaults to False.

        Returns:
            BytesIO: An in-memory byte stream of the generated .docx file.
        """
        document = Document()
        document.add_heading(title, level=1)

        # If the content is JSON, pretty-print it for readability
        if is_code:
            try:
                # Attempt to parse and re-format the JSON with indentation
                parsed_json = json.loads(content)
                pretty_content = json.dumps(parsed_json, indent=4)
            except json.JSONDecodeError:
                # If it's not valid JSON, just use the original content
                pretty_content = content

            p = document.add_paragraph()
            run = p.add_run(pretty_content)
            font = run.font
            font.name = 'Courier New'
            font.size = Pt(10)
        else:
            # For regular text, add it as paragraphs
            for para in content.split('\n'):
                document.add_paragraph(para)

        # Save document to an in-memory buffer
        doc_buffer = BytesIO()
        document.save(doc_buffer)
        doc_buffer.seek(0)
        return doc_buffer