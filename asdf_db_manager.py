import sqlite3
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List
import json
from datetime import datetime, timezone

@dataclass
class Artifact:
    """
    Represents a single work artifact in the Record-of-Work-Done (RoWD).
    This dataclass serves as an explicit data contract for artifact records.
    """
    artifact_id: str
    project_id: str
    status: str
    last_modified_timestamp: str
    artifact_name: str
    artifact_type: str
    file_path: Optional[str] = None
    signature: Optional[str] = None
    short_description: Optional[str] = None
    version: int = 1
    commit_hash: Optional[str] = None
    micro_spec_id: Optional[str] = None
    dependencies: Optional[str] = None
    unit_test_status: Optional[str] = None

class ASDFDBManager:
    """
    Data Access Object (DAO) for the ASDF SQLite database.
    This version is architected to be thread-safe by managing connections
    on a per-query basis.
    """
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._ensure_db_directory_exists()

    def _ensure_db_directory_exists(self):
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.error(f"Failed to create database directory for {self.db_path}: {e}")
            raise

    def _get_connection(self):
        """Creates and configures a new database connection."""
        conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _execute_query(self, query: str, params: tuple = (), fetch: str = "none"):
        """Establishes a connection, executes a query, and closes it."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                if fetch == "one":
                    return cursor.fetchone()
                elif fetch == "all":
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor
        except sqlite3.Error as e:
            logging.error(f"Database query failed: {e}\nQuery: {query}")
            raise

    def create_tables(self):
        create_projects_table = """
        CREATE TABLE IF NOT EXISTS Projects (
            project_id TEXT PRIMARY KEY, project_name TEXT NOT NULL, creation_timestamp TEXT NOT NULL,
            target_os TEXT, technology_stack TEXT, project_root_folder TEXT, apex_executable_name TEXT,
            project_brief_path TEXT, complexity_assessment_text TEXT, ux_spec_text TEXT,
            is_gui_project BOOLEAN NOT NULL DEFAULT 0, final_spec_text TEXT, tech_spec_text TEXT,
            is_build_automated BOOLEAN NOT NULL DEFAULT 1, build_script_file_name TEXT,
            coding_standard_text TEXT, development_plan_text TEXT, integration_plan_text TEXT,
            ui_test_plan_text TEXT, test_execution_command TEXT
        );"""
        self._execute_query(create_projects_table)
        create_cr_register_table = """
        CREATE TABLE IF NOT EXISTS ChangeRequestRegister (
            cr_id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL,
            request_type TEXT NOT NULL DEFAULT 'CHANGE_REQUEST', description TEXT NOT NULL,
            creation_timestamp TEXT NOT NULL, last_modified_timestamp TEXT, status TEXT NOT NULL,
            impact_rating TEXT, impact_analysis_details TEXT, impacted_artifact_ids TEXT,
            linked_cr_id INTEGER,
            FOREIGN KEY (project_id) REFERENCES Projects (project_id),
            FOREIGN KEY (linked_cr_id) REFERENCES ChangeRequestRegister (cr_id)
        );"""
        self._execute_query(create_cr_register_table)
        create_artifacts_table = """
        CREATE TABLE IF NOT EXISTS Artifacts (
            artifact_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            file_path TEXT,
            artifact_name TEXT NOT NULL,
            artifact_type TEXT NOT NULL,
            signature TEXT,
            short_description TEXT,
            version INTEGER NOT NULL DEFAULT 1,
            last_modified_timestamp TEXT NOT NULL,
            commit_hash TEXT,
            micro_spec_id TEXT,
            dependencies TEXT,
            unit_test_status TEXT,
            FOREIGN KEY (project_id) REFERENCES Projects (project_id)
        );"""
        self._execute_query(create_artifacts_table)
        create_orchestration_state_table = """
        CREATE TABLE IF NOT EXISTS OrchestrationState (
            state_id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL UNIQUE,
            current_phase TEXT, current_step TEXT, state_details TEXT, last_updated TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES Projects (project_id)
        );"""
        self._execute_query(create_orchestration_state_table)
        create_factory_config_table = "CREATE TABLE IF NOT EXISTS FactoryConfig ( key TEXT PRIMARY KEY, value TEXT, description TEXT );"
        self._execute_query(create_factory_config_table)
        create_factory_knowledge_base_table = """
        CREATE TABLE IF NOT EXISTS FactoryKnowledgeBase (
            entry_id INTEGER PRIMARY KEY AUTOINCREMENT, context TEXT NOT NULL, problem TEXT NOT NULL,
            solution TEXT NOT NULL, tags TEXT, creation_timestamp TEXT NOT NULL
        );"""
        self._execute_query(create_factory_knowledge_base_table)
        create_project_history_table = """
        CREATE TABLE IF NOT EXISTS ProjectHistory (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL,
            project_name TEXT NOT NULL, project_root_folder TEXT NOT NULL,
            archive_file_path TEXT NOT NULL, last_stop_timestamp TEXT NOT NULL
        );"""
        self._execute_query(create_project_history_table)
        create_factory_templates_table = """
        CREATE TABLE IF NOT EXISTS FactoryTemplates (
            template_id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_name TEXT NOT NULL UNIQUE,
            file_path TEXT NOT NULL,
            creation_timestamp TEXT NOT NULL
        );"""
        self._execute_query(create_factory_templates_table)
        logging.info("Finished creating/verifying database tables.")

    def create_project(self, project_id: str, project_name: str, creation_timestamp: str) -> str:
        self._execute_query("INSERT INTO Projects (project_id, project_name, creation_timestamp) VALUES (?, ?, ?)", (project_id, project_name, creation_timestamp))
        return project_id

    def get_project_by_id(self, project_id: str) -> Optional[sqlite3.Row]:
        return self._execute_query("SELECT * FROM Projects WHERE project_id = ?", (project_id,), fetch="one")

    def delete_project_by_id(self, project_id: str):
        self._execute_query("DELETE FROM Projects WHERE project_id = ?", (project_id,))

    def create_or_update_project_record(self, project_data: dict):
        if 'project_id' not in project_data: raise ValueError("project_data must contain 'project_id' for an upsert operation.")
        columns, placeholders = ', '.join(project_data.keys()), ', '.join('?' * len(project_data))
        self._execute_query(f"INSERT OR REPLACE INTO Projects ({columns}) VALUES ({placeholders})", tuple(project_data.values()))

    def update_project_field(self, project_id: str, field_name: str, value: any):
        self._execute_query(f"UPDATE Projects SET {field_name} = ? WHERE project_id = ?", (value, project_id))

    def get_artifact_by_id(self, artifact_id: str) -> Optional[sqlite3.Row]:
        return self._execute_query("SELECT * FROM Artifacts WHERE artifact_id = ?", (artifact_id,), fetch="one")

    def get_all_artifacts_for_project(self, project_id: str) -> List[sqlite3.Row]:
        return self._execute_query("SELECT * FROM Artifacts WHERE project_id = ? ORDER BY artifact_name", (project_id,), fetch="all")

    def get_component_counts_by_status(self, project_id: str) -> dict[str, int]:
        rows = self._execute_query("SELECT status, COUNT(*) FROM Artifacts WHERE project_id = ? GROUP BY status", (project_id,), fetch="all")
        return {row[0]: row[1] for row in rows} if rows else {}

    def get_artifacts_by_statuses(self, project_id: str, statuses: list[str]) -> list[sqlite3.Row]:
        if not statuses: return []
        placeholders = ', '.join('?' for _ in statuses)
        query = f"SELECT * FROM Artifacts WHERE project_id = ? AND status IN ({placeholders})"
        params = (project_id,) + tuple(statuses)
        return self._execute_query(query, params, fetch="all")

    def add_or_update_artifact(self, artifact_data: dict):
        if 'artifact_id' not in artifact_data: raise ValueError("artifact_data must contain 'artifact_id'.")
        columns, placeholders = ', '.join(artifact_data.keys()), ', '.join('?' * len(artifact_data))
        self._execute_query(f"INSERT OR REPLACE INTO Artifacts ({columns}) VALUES ({placeholders})", tuple(artifact_data.values()))

    def delete_all_artifacts_for_project(self, project_id: str):
        self._execute_query("DELETE FROM Artifacts WHERE project_id = ?", (project_id,))

    def bulk_insert_artifacts(self, artifacts_data: list[dict]):
        if not artifacts_data: return
        try:
            with self._get_connection() as conn:
                columns, placeholders = ', '.join(artifacts_data[0].keys()), ', '.join('?' * len(artifacts_data[0]))
                query = f"INSERT INTO Artifacts ({columns}) VALUES ({placeholders})"
                params = [tuple(d.values()) for d in artifacts_data]
                conn.executemany(query, params)
        except sqlite3.Error as e:
            logging.error(f"Bulk artifact insert failed: {e}")
            raise

    def set_config_value(self, key: str, value: str, description: Optional[str] = None):
        if description is None:
            current_desc_row = self._execute_query("SELECT description FROM FactoryConfig WHERE key = ?", (key,), fetch="one")
            description = current_desc_row[0] if current_desc_row and current_desc_row[0] else ""
        self._execute_query("INSERT OR REPLACE INTO FactoryConfig (key, value, description) VALUES (?, ?, ?)", (key, str(value), description))

    def get_config_value(self, key: str) -> Optional[str]:
        row = self._execute_query("SELECT value FROM FactoryConfig WHERE key = ?", (key,), fetch="one")
        return row[0] if row else None

    def get_all_config_values(self) -> dict[str, str]:
        rows = self._execute_query("SELECT key, value FROM FactoryConfig", fetch="all")
        return {row[0]: row[1] for row in rows} if rows else {}

    def add_project_to_history(self, project_id: str, project_name: str, root_folder: str, archive_path: str, timestamp: str):
        self._execute_query("INSERT INTO ProjectHistory (project_id, project_name, project_root_folder, archive_file_path, last_stop_timestamp) VALUES (?, ?, ?, ?, ?)", (project_id, project_name, root_folder, archive_path, timestamp))

    def get_project_history(self) -> list[sqlite3.Row]:
        return self._execute_query("SELECT * FROM ProjectHistory ORDER BY last_stop_timestamp DESC", fetch="all")

    def get_project_history_by_id(self, history_id: int) -> Optional[sqlite3.Row]:
        return self._execute_query("SELECT * FROM ProjectHistory WHERE history_id = ?", (history_id,), fetch="one")

    def delete_project_from_history(self, history_id: int):
        self._execute_query("DELETE FROM ProjectHistory WHERE history_id = ?", (history_id,))

    def add_template(self, template_name: str, file_path: str) -> int:
        """Adds a new template record to the database."""
        timestamp = datetime.now(timezone.utc).isoformat()
        query = "INSERT INTO FactoryTemplates (template_name, file_path, creation_timestamp) VALUES (?, ?, ?)"
        cursor = self._execute_query(query, (template_name, file_path, timestamp))
        return cursor.lastrowid

    def get_template_by_name(self, template_name: str) -> Optional[sqlite3.Row]:
        """Retrieves a specific template record by its unique name."""
        query = "SELECT * FROM FactoryTemplates WHERE template_name = ?"
        return self._execute_query(query, (template_name,), fetch="one")

    def get_all_templates(self) -> list:
        """Retrieves all saved template records from the database."""
        query = "SELECT * FROM FactoryTemplates ORDER BY template_name"
        return self._execute_query(query, fetch="all")

    def delete_template(self, template_id: int):
        """Deletes a template record from the database by its ID."""
        query = "DELETE FROM FactoryTemplates WHERE template_id = ?"
        self._execute_query(query, (template_id,))

    def get_all_change_requests_for_project(self, project_id: str) -> list:
        return self._execute_query("SELECT * FROM ChangeRequestRegister WHERE project_id = ? ORDER BY creation_timestamp DESC", (project_id,), fetch="all")

    def add_change_request(self, project_id: str, description: str, request_type: str = 'CHANGE_REQUEST') -> int:
        timestamp = datetime.now(timezone.utc).isoformat()
        cursor = self._execute_query("INSERT INTO ChangeRequestRegister (project_id, description, creation_timestamp, status, request_type) VALUES (?, ?, ?, ?, ?)", (project_id, description, timestamp, "RAISED", request_type))
        return cursor.lastrowid

    def add_bug_report(self, project_id: str, description: str, severity: str) -> int:
        timestamp = datetime.now(timezone.utc).isoformat()
        cursor = self._execute_query("INSERT INTO ChangeRequestRegister (project_id, request_type, description, creation_timestamp, status, impact_rating) VALUES (?, ?, ?, ?, ?, ?)", (project_id, 'BUG_REPORT', description, timestamp, 'RAISED', severity))
        return cursor.lastrowid

    def delete_all_change_requests_for_project(self, project_id: str):
        self._execute_query("DELETE FROM ChangeRequestRegister WHERE project_id = ?", (project_id,))

    def bulk_insert_change_requests(self, cr_data: list[dict]):
        if not cr_data: return
        try:
            with self._get_connection() as conn:
                columns, placeholders = ', '.join(cr_data[0].keys()), ', '.join('?' * len(cr_data[0]))
                query = f"INSERT INTO ChangeRequestRegister ({columns}) VALUES ({placeholders})"
                params = [tuple(d.values()) for d in cr_data]
                conn.executemany(query, params)
        except sqlite3.Error as e:
            logging.error(f"Bulk CR insert failed: {e}")
            raise

    def get_cr_by_id(self, cr_id: int):
        return self._execute_query("SELECT * FROM ChangeRequestRegister WHERE cr_id = ?", (cr_id,), fetch="one")

    def save_orchestration_state(self, project_id: str, current_phase: str, current_step: str, state_details: str, timestamp: str):
        self._execute_query("INSERT OR REPLACE INTO OrchestrationState (project_id, current_phase, current_step, state_details, last_updated) VALUES (?, ?, ?, ?, ?)", (project_id, current_phase, current_step, state_details, timestamp))

    def get_any_paused_state(self) -> Optional[sqlite3.Row]:
        return self._execute_query("SELECT * FROM OrchestrationState LIMIT 1", fetch="one")

    def delete_orchestration_state_for_project(self, project_id: str):
        self._execute_query("DELETE FROM OrchestrationState WHERE project_id = ?", (project_id,))

    def add_kb_entry(self, context: str, problem: str, solution: str, tags: str, timestamp: str):
        self._execute_query("INSERT INTO FactoryKnowledgeBase (context, problem, solution, tags, creation_timestamp) VALUES (?, ?, ?, ?, ?)", (context, problem, solution, tags, timestamp))

    def query_kb_by_tags(self, tags: list[str]) -> list[sqlite3.Row]:
        if not tags: return []
        likes, params = ' OR '.join(['tags LIKE ?' for _ in tags]), [f'%{tag}%' for tag in tags]
        return self._execute_query(f"SELECT * FROM FactoryKnowledgeBase WHERE {likes}", tuple(params), fetch="all")

    # The following methods from the original file need to be added back in, refactored.
    def update_cr_impact_analysis(self, cr_id: int, rating: str, details: str, artifact_ids: list[str]):
        ids_json = json.dumps(artifact_ids)
        timestamp = datetime.now(timezone.utc).isoformat()
        query = "UPDATE ChangeRequestRegister SET impact_rating = ?, impact_analysis_details = ?, impacted_artifact_ids = ?, status = 'IMPACT_ANALYZED', last_modified_timestamp = ? WHERE cr_id = ?"
        self._execute_query(query, (rating, details, ids_json, timestamp, cr_id))

    def update_cr_status(self, cr_id: int, new_status: str):
        timestamp = datetime.now(timezone.utc).isoformat()
        query = "UPDATE ChangeRequestRegister SET status = ?, last_modified_timestamp = ? WHERE cr_id = ?"
        self._execute_query(query, (new_status, timestamp, cr_id))

    def update_change_request(self, cr_id: int, new_description: str):
        timestamp = datetime.now(timezone.utc).isoformat()
        query = "UPDATE ChangeRequestRegister SET description = ?, impact_rating = NULL, impact_analysis_details = NULL, last_modified_timestamp = ? WHERE cr_id = ?"
        self._execute_query(query, (new_description, timestamp, cr_id))

    def get_cr_by_linked_id(self, parent_cr_id: int):
        return self._execute_query("SELECT * FROM ChangeRequestRegister WHERE linked_cr_id = ?", (parent_cr_id,), fetch="one")

    def delete_change_request(self, cr_id: int):
        self._execute_query("DELETE FROM ChangeRequestRegister WHERE cr_id = ?", (cr_id,))

    def get_change_requests_by_statuses(self, project_id: str, statuses: list[str]) -> list:
        if not statuses: return []
        placeholders = ', '.join('?' for _ in statuses)
        query = f"SELECT * FROM ChangeRequestRegister WHERE project_id = ? AND status IN ({placeholders}) ORDER BY creation_timestamp DESC"
        params = (project_id,) + tuple(statuses)
        return self._execute_query(query, params, fetch="all")

    def update_artifact_status(self, artifact_id: str, status: str, timestamp: str):
        query = "UPDATE Artifacts SET status = ?, last_modified_timestamp = ? WHERE artifact_id = ?"
        self._execute_query(query, (status, timestamp, artifact_id))