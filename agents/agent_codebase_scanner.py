# agents/agent_codebase_scanner.py

import logging
import time
import hashlib
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from llm_service import LLMService
from asdf_db_manager import ASDFDBManager
from agents.agent_code_summarization import CodeSummarizationAgent
from agents.doc_update_agent_rowd import DocUpdateAgentRoWD

class CodebaseScannerAgent:
    """
    Agent responsible for scanning a local codebase, summarizing each file,
    and populating the Record-of-Work-Done (RoWD) in the database.
    """

    def __init__(self, llm_service: LLMService, db_manager: ASDFDBManager):
        if not llm_service:
            raise ValueError("llm_service is required for the CodebaseScannerAgent.")
        if not db_manager:
            raise ValueError("db_manager is required for the CodebaseScannerAgent.")
        self.llm_service = llm_service
        self.db_manager = db_manager
        self.summarization_agent = CodeSummarizationAgent(self.llm_service)
        self.doc_update_agent = DocUpdateAgentRoWD(self.db_manager, self.llm_service)
        logging.info("CodebaseScannerAgent initialized.")

    def scan_project(self, project_id: str, root_path_str: str, pause_event: threading.Event, progress_callback, worker_instance):
        """
        Scans a project directory, processes each file, and saves the summary,
        emitting structured progress updates.
        """
        root_path = Path(root_path_str)
        source_extensions = ['.py', '.js', '.ts', '.html', '.css', '.scss', '.java', '.kt', '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.ui']

        all_files = [p for p in root_path.rglob('*') if p.is_file() and p.suffix.lower() in source_extensions]
        total_files = len(all_files)
        logging.info(f"Found {total_files} source files to analyze.")
        progress_callback(("SCANNING", {"total_files": total_files}))

        for i, file_path in enumerate(all_files):
            if worker_instance.is_cancelled:
                logging.warning("Cancellation signal received. Aborting scan.")
                return False

            if pause_event.is_set():
                logging.info(f"Analysis paused at file {i+1}/{total_files}.")
                pause_event.wait()
                logging.info("Analysis resumed.")

            relative_path_str = str(file_path.relative_to(root_path)).replace('\\', '/')

            # Emit the correctly structured data
            progress_callback(("SUMMARIZING", {"total": total_files, "current": i + 1, "filename": relative_path_str}))

            existing_artifact = self.db_manager.get_artifact_by_path(project_id, relative_path_str)
            if existing_artifact and existing_artifact['code_summary']:
                logging.info(f"Skipping already summarized file: {relative_path_str}")
                continue

            try:
                content = file_path.read_text(encoding='utf-8')
                summary = "Qt Designer UI file." if file_path.suffix.lower() == '.ui' else self.summarization_agent.summarize_code(content)
                if "Error:" in summary:
                    logging.warning(f"Could not generate summary for {relative_path_str}. Skipping.")
                    continue

                file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
                artifact_data = {
                    "artifact_id": f"art_{uuid.uuid4().hex[:8]}",
                    "project_id": project_id,
                    "file_path": relative_path_str,
                    "artifact_name": file_path.name,
                    "artifact_type": "EXISTING_CODE",
                    "code_summary": summary,
                    "file_hash": file_hash,
                    "status": "ANALYZED",
                    "last_modified_timestamp": datetime.now(timezone.utc).isoformat(),
                }
                self.db_manager.add_brownfield_artifact(artifact_data)

            except Exception as e:
                logging.error(f"Failed to process file {relative_path_str}: {e}")

        logging.info("Codebase scan and summarization complete.")
        return True