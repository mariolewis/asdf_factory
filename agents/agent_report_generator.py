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
import pandas as pd
from datetime import datetime

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

    def generate_assessment_docx(self, analysis_data: dict, project_name: str) -> BytesIO:
        """
        Generates a formatted .docx file for the Complexity & Risk Assessment report.

        Args:
            analysis_data (dict): The structured data from the ProjectScopingAgent.
            project_name (str): The name of the project for the report title.

        Returns:
            BytesIO: An in-memory byte stream of the generated .docx file.
        """
        document = Document()
        document.add_heading(f"Complexity & Risk Assessment: {project_name}", level=1)

        if not analysis_data or "complexity_analysis" not in analysis_data:
            document.add_paragraph("Could not parse the analysis result.")
        else:
            # --- Complexity Analysis Section ---
            document.add_heading('Complexity Analysis', level=2)
            comp_analysis = analysis_data.get("complexity_analysis", {})
            for key, value in comp_analysis.items():
                title = key.replace('_', ' ').title()
                rating = value.get('rating', 'N/A')
                justification = value.get('justification', 'No details provided.')

                p = document.add_paragraph()
                p.add_run(f"{title}: ").bold = True
                p.add_run(rating)
                document.add_paragraph(justification, style='Intense Quote')

            # --- Risk Assessment Section ---
            document.add_heading('Risk Assessment', level=2)
            risk_assessment = analysis_data.get("risk_assessment", {})

            p_risk = document.add_paragraph()
            p_risk.add_run("Overall Risk Level: ").bold = True
            p_risk.add_run(risk_assessment.get('overall_risk_level', 'N/A'))

            p_summary = document.add_paragraph()
            p_summary.add_run("Summary: ").bold = True
            p_summary.add_run(risk_assessment.get('summary', 'No summary provided.'))

            p_token = document.add_paragraph()
            p_token.add_run("Token Consumption Outlook: ").bold = True
            p_token.add_run(risk_assessment.get('token_consumption_outlook', 'N/A'))

            recommendations = risk_assessment.get('recommendations', [])
            if recommendations:
                document.add_paragraph("Recommendations:", style='Heading 3')
                for rec in recommendations:
                    document.add_paragraph(rec, style='List Bullet')

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

    def generate_dev_plan_docx(self, plan_data: dict, project_name: str) -> BytesIO:
        """
        Generates a formatted .docx file for the Development Plan.

        Args:
            plan_data (dict): The structured data for the development plan.
            project_name (str): The name of the project for the report title.

        Returns:
            BytesIO: An in-memory byte stream of the generated .docx file.
        """
        document = Document()
        document.add_heading(f"Development Plan: {project_name}", level=1)

        main_exe = plan_data.get("main_executable_file", "Not specified")
        document.add_paragraph(f"Main Executable File: {main_exe}")

        document.add_heading('Development Steps', level=2)

        plan_steps = plan_data.get("development_plan", [])
        if not plan_steps:
            document.add_paragraph("No development steps were generated.")
        else:
            for i, task in enumerate(plan_steps, 1):
                p = document.add_paragraph(style='List Number')
                run = p.add_run(f"Task {i}: {task.get('component_name', 'N/A')}")
                run.bold = True

                # Add details with indentation
                p_desc = document.add_paragraph(f"Description: {task.get('task_description', 'No description.')}")
                p_desc.paragraph_format.left_indent = Inches(0.25)

                p_id = document.add_paragraph(f"ID: {task.get('micro_spec_id', 'N/A')}")
                p_id.paragraph_format.left_indent = Inches(0.25)

        # Save document to an in-memory buffer
        doc_buffer = BytesIO()
        document.save(doc_buffer)
        doc_buffer.seek(0)
        return doc_buffer

    def generate_backlog_xlsx(self, backlog_data: list) -> BytesIO:
        """
        Generates an .xlsx file for the full project backlog.

        Args:
            backlog_data (list): The hierarchical list of backlog item dictionaries.

        Returns:
            BytesIO: An in-memory byte stream of the generated .xlsx file.
        """
        flat_list = []

        def flatten_hierarchy(items, prefix=""):
            for i, item in enumerate(items, 1):
                current_prefix = f"{prefix}{i}"

                timestamp_str = item.get('last_modified_timestamp') or item.get('creation_timestamp')
                formatted_date = ""
                if timestamp_str:
                    try:
                        dt_object = datetime.fromisoformat(timestamp_str)
                        formatted_date = dt_object.strftime('%Y-%m-%d %H:%M')
                    except ValueError:
                        formatted_date = timestamp_str.split('T')[0]

                record = {
                    '#': current_prefix,
                    'Title': item.get('title', 'N/A'),
                    'Type': item.get('request_type', 'N/A').replace('_', ' ').title(),
                    'Status': item.get('status', 'N/A'),
                    'Priority/Severity': item.get('priority') or item.get('impact_rating') or '',
                    'Complexity': item.get('complexity', ''),
                    'Last Modified': formatted_date
                }
                flat_list.append(record)

                if "features" in item:
                    flatten_hierarchy(item["features"], prefix=f"{current_prefix}.")
                if "user_stories" in item:
                    flatten_hierarchy(item["user_stories"], prefix=f"{current_prefix}.")

        flatten_hierarchy(backlog_data)

        df = pd.DataFrame(flat_list)

        # Save dataframe to an in-memory buffer
        output_buffer = BytesIO()
        with pd.ExcelWriter(output_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Project Backlog')

        output_buffer.seek(0)
        return output_buffer

    def generate_sprint_plan_docx(self, project_name: str, sprint_items: list, plan_data: list) -> BytesIO:
        """
        Generates a formatted .docx file for the Sprint Plan.

        Args:
            project_name (str): The name of the project.
            sprint_items (list): The list of backlog items in the sprint scope.
            plan_data (list): The list of development tasks in the plan.

        Returns:
            BytesIO: An in-memory byte stream of the generated .docx file.
        """
        document = Document()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        document.add_heading(f"Sprint Plan: {project_name}", level=1)
        document.add_paragraph(f"Generated on: {timestamp}")

        document.add_heading('Sprint Scope', level=2)
        if not sprint_items:
            document.add_paragraph("No items were included in this sprint.")
        else:
            for item in sprint_items:
                document.add_paragraph(item.get('title', 'Untitled Item'), style='List Bullet')

        document.add_heading('Implementation Plan', level=2)
        if not plan_data or (isinstance(plan_data, list) and plan_data and plan_data[0].get("error")):
            document.add_paragraph("No implementation plan was generated.")
        else:
            for i, task in enumerate(plan_data, 1):
                p = document.add_paragraph()
                p.add_run(f"Task {i}: {task.get('component_name', 'N/A')}").bold = True

                document.add_paragraph(f"File Path: {task.get('component_file_path', 'N/A')}")
                p_desc = document.add_paragraph(f"Description: {task.get('task_description', 'No description.')}")
                p_desc.paragraph_format.left_indent = Inches(0.25)

        # Save document to an in-memory buffer
        doc_buffer = BytesIO()
        document.save(doc_buffer)
        doc_buffer.seek(0)
        return doc_buffer