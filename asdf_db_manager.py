import sqlite3
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List
import json
from datetime import datetime, timezone

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    dependencies: Optional[str] = None  # Stored as a JSON string list
    unit_test_status: Optional[str] = None

class ASDFDBManager:
    """
    Data Access Object (DAO) for the ASDF SQLite database.

    This class handles all database interactions, providing a dedicated interface
    for creating, reading, updating, and deleting records in the ASDF database.
    It encapsulates all SQL queries and manages the database connection.
    """

    def __init__(self, db_path: str | Path):
        """
        Initializes the database manager.

        Args:
            db_path (str | Path): The path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self._ensure_db_directory_exists()
        self.conn = None

    def _ensure_db_directory_exists(self):
        """Ensures that the directory for the database file exists."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            logging.info(f"Database directory ensured at: {self.db_path.parent}")
        except Exception as e:
            logging.error(f"Failed to create database directory for {self.db_path}: {e}")
            raise

    def __enter__(self):
        """Establishes the database connection."""
        try:
            # CORRECTED: Added check_same_thread=False to allow access from multiple threads
            # in the Streamlit environment. This is critical for preventing deadlocks.
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row # Allows accessing columns by name
            logging.info(f"Database connection established to: {self.db_path}")
            return self
        except sqlite3.Error as e:
            logging.error(f"Error connecting to database {self.db_path}: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            logging.info(f"Database connection closed.")

    def _execute_query(self, query: str, params: tuple = ()):
        """
        Executes a given SQL query.

        Args:
            query (str): The SQL query to execute.
            params (tuple, optional): The parameters to substitute into the query. Defaults to ().

        Returns:
            sqlite3.Cursor: The cursor object after execution.
        """
        if not self.conn:
            raise ConnectionError("Database connection is not open. Use 'with' statement.")

        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return cursor
        except sqlite3.Error as e:
            logging.error(f"Database query failed: {e}\nQuery: {query}")
            self.conn.rollback()
            raise

    def create_tables(self):
        """
        Creates all necessary tables in the database if they do not already exist.
        This method is idempotent.
        """
        logging.info("Attempting to create database tables if they don't exist.")

        create_projects_table = """
        CREATE TABLE IF NOT EXISTS Projects (
            project_id TEXT PRIMARY KEY,
            project_name TEXT NOT NULL,
            creation_timestamp TEXT NOT NULL,
            target_os TEXT,
            technology_stack TEXT,
            project_root_folder TEXT,
            apex_executable_name TEXT,
            complexity_assessment_text TEXT,
            final_spec_text TEXT,
            tech_spec_text TEXT,
            is_build_automated BOOLEAN NOT NULL DEFAULT 1,
            coding_standard_text TEXT,
            development_plan_text TEXT,
            integration_plan_text TEXT,
            ui_test_plan_text TEXT,
            test_execution_command TEXT
        );
        """
        self._execute_query(create_projects_table)

        create_cr_register_table = """
        CREATE TABLE IF NOT EXISTS ChangeRequestRegister (
            cr_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL,
            request_type TEXT NOT NULL DEFAULT 'CHANGE_REQUEST',
            description TEXT NOT NULL,
            creation_timestamp TEXT NOT NULL,
            last_modified_timestamp TEXT,
            status TEXT NOT NULL,
            impact_rating TEXT,
            impact_analysis_details TEXT,
            impacted_artifact_ids TEXT,
            linked_cr_id INTEGER,
            FOREIGN KEY (project_id) REFERENCES Projects (project_id),
            FOREIGN KEY (linked_cr_id) REFERENCES ChangeRequestRegister (cr_id)
        );
        """
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
            status TEXT NOT NULL,
            last_modified_timestamp TEXT NOT NULL,
            commit_hash TEXT,
            micro_spec_id TEXT,
            dependencies TEXT,
            unit_test_status TEXT,
            FOREIGN KEY (project_id) REFERENCES Projects (project_id)
        );
        """
        self._execute_query(create_artifacts_table)

        create_orchestration_state_table = """
        CREATE TABLE IF NOT EXISTS OrchestrationState (
            state_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL UNIQUE,
            current_phase TEXT,
            current_step TEXT,
            state_details TEXT, -- JSON blob for detailed state
            last_updated TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES Projects (project_id)
        );
        """
        self._execute_query(create_orchestration_state_table)

        create_factory_config_table = """
        CREATE TABLE IF NOT EXISTS FactoryConfig (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT
        );
        """
        self._execute_query(create_factory_config_table)

        create_factory_knowledge_base_table = """
        CREATE TABLE IF NOT EXISTS FactoryKnowledgeBase (
            entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            context TEXT NOT NULL,
            problem TEXT NOT NULL,
            solution TEXT NOT NULL,
            tags TEXT,
            creation_timestamp TEXT NOT NULL
        );
        """
        self._execute_query(create_factory_knowledge_base_table)

        create_project_history_table = """
        CREATE TABLE IF NOT EXISTS ProjectHistory (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL,
            project_name TEXT NOT NULL,
            project_root_folder TEXT NOT NULL,
            archive_file_path TEXT NOT NULL,
            last_stop_timestamp TEXT NOT NULL
        );
        """
        self._execute_query(create_project_history_table)

        logging.info("Finished creating database tables.")

    # --- Project CRUD Operations ---

    def create_project(self, project_id: str, project_name: str, creation_timestamp: str) -> str:
        """
        Creates a new project record in the Projects table.
        """
        query = "INSERT INTO Projects (project_id, project_name, creation_timestamp) VALUES (?, ?, ?)"
        params = (project_id, project_name, creation_timestamp)
        self._execute_query(query, params)
        logging.info(f"Created new project '{project_name}' with ID '{project_id}'.")
        return project_id

    def get_project_by_id(self, project_id: str) -> sqlite3.Row | None:
        """
        Retrieves a single project record by its ID.
        """
        query = "SELECT * FROM Projects WHERE project_id = ?"
        cursor = self._execute_query(query, (project_id,))
        return cursor.fetchone()

    def save_final_specification(self, project_id: str, spec_text: str):
        """
        Saves the finalized specification text to the project's record.
        """
        query = "UPDATE Projects SET final_spec_text = ? WHERE project_id = ?"
        params = (spec_text, project_id)
        self._execute_query(query, params)
        logging.info(f"Saved final specification for project ID '{project_id}'.")

    def save_complexity_assessment(self, project_id: str, assessment_text: str):
        """
        Saves the complexity and risk assessment text to the project's record.
        """
        query = "UPDATE Projects SET complexity_assessment_text = ? WHERE project_id = ?"
        params = (assessment_text, project_id)
        self._execute_query(query, params)
        logging.info(f"Saved complexity assessment for project ID '{project_id}'.")

    def save_tech_specification(self, project_id: str, tech_spec_text: str):
        """
        Saves the formal Technical Specification Document text to the project's record.
        """
        query = "UPDATE Projects SET tech_spec_text = ? WHERE project_id = ?"
        params = (tech_spec_text, project_id)
        self._execute_query(query, params)
        logging.info(f"Saved technical specification for project ID '{project_id}'.")

    def save_coding_standard(self, project_id: str, standard_text: str):
        """
        Saves the approved Coding Standard text to the project's record.
        """
        query = "UPDATE Projects SET coding_standard_text = ? WHERE project_id = ?"
        params = (standard_text, project_id)
        self._execute_query(query, params)
        logging.info(f"Saved coding standard for project ID '{project_id}'.")

    def save_development_plan(self, project_id: str, plan_text: str):
        """
        Saves the approved Development Plan text to the project's record.
        """
        query = "UPDATE Projects SET development_plan_text = ? WHERE project_id = ?"
        params = (plan_text, project_id)
        self._execute_query(query, params)
        logging.info(f"Saved development plan for project ID '{project_id}'.")

    def save_integration_plan(self, project_id: str, plan_text: str):
        """
        Saves the generated Integration Plan text to the project's record.
        """
        query = "UPDATE Projects SET integration_plan_text = ? WHERE project_id = ?"
        params = (plan_text, project_id)
        self._execute_query(query, params)
        logging.info(f"Saved integration plan for project ID '{project_id}'.")

    def save_ui_test_plan(self, project_id: str, plan_text: str):
        """
        Saves the generated UI Test Plan text to the project's record.
        """
        query = "UPDATE Projects SET ui_test_plan_text = ? WHERE project_id = ?"
        params = (plan_text, project_id)
        self._execute_query(query, params)
        logging.info(f"Saved UI test plan for project ID '{project_id}'.")

    def update_project_technology(self, project_id: str, technology_stack: str):
        """
        Updates the technology_stack for a given project.
        """
        query = "UPDATE Projects SET technology_stack = ? WHERE project_id = ?"
        params = (technology_stack, project_id)
        self._execute_query(query, params)
        logging.info(f"Set technology stack for project ID '{project_id}' to '{technology_stack}'.")

    def update_project_apex_file(self, project_id: str, apex_name: str):
        """
        Updates the apex_executable_name for a given project.
        """
        query = "UPDATE Projects SET apex_executable_name = ? WHERE project_id = ?"
        params = (apex_name, project_id)
        self._execute_query(query, params)
        logging.info(f"Set apex file for project ID '{project_id}' to '{apex_name}'.")

    def update_project_root_folder(self, project_id: str, path: str):
        """
        Updates the project_root_folder for a given project.
        """
        query = "UPDATE Projects SET project_root_folder = ? WHERE project_id = ?"
        params = (path, project_id)
        self._execute_query(query, params)
        logging.info(f"Set project root folder for project ID '{project_id}' to '{path}'.")

    def update_project_build_automation_status(self, project_id: str, is_automated: bool):
        """
        Updates the build automation status for a given project.
        """
        status_as_int = 1 if is_automated else 0
        query = "UPDATE Projects SET is_build_automated = ? WHERE project_id = ?"
        params = (status_as_int, project_id)
        self._execute_query(query, params)
        logging.info(f"Set build automation status for project ID '{project_id}' to {is_automated}.")

    def update_project_test_command(self, project_id: str, command: str):
        """
        Saves the PM-confirmed test execution command for the project.
        """
        query = "UPDATE Projects SET test_execution_command = ? WHERE project_id = ?"
        params = (command, project_id)
        self._execute_query(query, params)
        logging.info(f"Set test execution command for project ID '{project_id}'.")

    def update_project_os(self, project_id: str, target_os: str):
        """
        Saves the selected target Operating System for the project.
        """
        query = "UPDATE Projects SET target_os = ? WHERE project_id = ?"
        params = (target_os, project_id)
        self._execute_query(query, params)
        logging.info(f"Set target OS for project ID '{project_id}' to '{target_os}'.")

    # --- Artifact (RoWD) CRUD Operations ---

    def create_artifact(self, artifact: Artifact):
        """
        Creates a new artifact record in the Artifacts table from an Artifact object.
        """
        artifact_dict = asdict(artifact)
        columns = ', '.join(artifact_dict.keys())
        placeholders = ', '.join('?' for _ in artifact_dict)
        query = f"INSERT INTO Artifacts ({columns}) VALUES ({placeholders})"
        params = tuple(artifact_dict.values())
        self._execute_query(query, params)
        logging.info(f"Created artifact '{artifact.artifact_name}' with ID '{artifact.artifact_id}'.")

    def get_artifact_by_id(self, artifact_id: str) -> sqlite3.Row | None:
        """
        Retrieves a single artifact by its ID.
        """
        query = "SELECT * FROM Artifacts WHERE artifact_id = ?"
        cursor = self._execute_query(query, (artifact_id,))
        return cursor.fetchone()

    def get_artifact_by_name(self, project_id: str, artifact_name: str) -> Optional[sqlite3.Row]:
        """Retrieves a single artifact by its name for a given project."""
        query = "SELECT * FROM Artifacts WHERE project_id = ? AND artifact_name = ?"
        cursor = self._execute_query(query, (project_id, artifact_name))
        return cursor.fetchone()

    def update_artifact_status(self, artifact_id: str, status: str, timestamp: str):
        """
        Updates the status and timestamp of a specific artifact.
        """
        query = "UPDATE Artifacts SET status = ?, last_modified_timestamp = ? WHERE artifact_id = ?"
        params = (status, timestamp, artifact_id)
        self._execute_query(query, params)
        logging.info(f"Updated status for artifact ID '{artifact_id}' to '{status}'.")

    def get_component_counts_by_status(self, project_id: str) -> dict[str, int]:
        """
        Gets the count of artifacts for each status for a given project.
        """
        query = "SELECT status, COUNT(*) FROM Artifacts WHERE project_id = ? GROUP BY status"
        cursor = self._execute_query(query, (project_id,))
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}
        logging.info(f"Retrieved component counts for project ID '{project_id}': {status_counts}")
        return status_counts

    def get_artifacts_by_statuses(self, project_id: str, statuses: list[str]) -> list[sqlite3.Row]:
        """
        Retrieves all artifacts for a project that match a list of statuses.
        """
        if not statuses:
            return []
        placeholders = ', '.join('?' for _ in statuses)
        query = f"SELECT * FROM Artifacts WHERE project_id = ? AND status IN ({placeholders})"
        params = (project_id,) + tuple(statuses)
        cursor = self._execute_query(query, params)
        return cursor.fetchall()

    def get_all_artifacts_for_project(self, project_id: str) -> list[sqlite3.Row]:
        """
        Retrieves all artifact records for a given project, ordered by name.
        """
        query = "SELECT * FROM Artifacts WHERE project_id = ? ORDER BY artifact_name"
        cursor = self._execute_query(query, (project_id,))
        return cursor.fetchall()

    def delete_all_artifacts_for_project(self, project_id: str):
        """
        Deletes all artifact records for a given project from the Artifacts table.
        """
        query = "DELETE FROM Artifacts WHERE project_id = ?"
        self._execute_query(query, (project_id,))
        logging.info(f"Deleted all RoWD artifacts for project ID '{project_id}'.")

    def delete_all_change_requests_for_project(self, project_id: str):
        """
        Deletes all change requests for a given project.
        """
        query = "DELETE FROM ChangeRequestRegister WHERE project_id = ?"
        self._execute_query(query, (project_id,))
        logging.info(f"Deleted all Change Requests for project ID '{project_id}'.")

    def delete_orchestration_state_for_project(self, project_id: str):
        """
        Deletes the orchestration state record for a given project.
        """
        query = "DELETE FROM OrchestrationState WHERE project_id = ?"
        self._execute_query(query, (project_id,))
        logging.info(f"Deleted Orchestration State for project ID '{project_id}'.")

    def bulk_insert_artifacts(self, artifacts_data: list[dict]):
        """
        Inserts multiple artifact records into the database.
        """
        if not artifacts_data:
            return
        columns = ', '.join(artifacts_data[0].keys())
        placeholders = ', '.join('?' for _ in artifacts_data[0])
        query = f"INSERT INTO Artifacts ({columns}) VALUES ({placeholders})"
        params = [tuple(d.values()) for d in artifacts_data]
        if not self.conn:
            raise ConnectionError("Database connection is not open. Use 'with' statement.")
        try:
            cursor = self.conn.cursor()
            cursor.executemany(query, params)
            self.conn.commit()
            logging.info(f"Bulk inserted {len(artifacts_data)} artifacts.")
        except sqlite3.Error as e:
            logging.error(f"Bulk artifact insert failed: {e}\nQuery: {query}")
            self.conn.rollback()
            raise

    def bulk_insert_change_requests(self, cr_data: list[dict]):
        """
        Inserts multiple change request records into the database.
        """
        if not cr_data:
            return
        columns = ', '.join(cr_data[0].keys())
        placeholders = ', '.join('?' for _ in cr_data[0])
        query = f"INSERT INTO ChangeRequestRegister ({columns}) VALUES ({placeholders})"
        params = [tuple(d.values()) for d in cr_data]
        if not self.conn:
            raise ConnectionError("Database connection is not open. Use 'with' statement.")
        try:
            cursor = self.conn.cursor()
            cursor.executemany(query, params)
            self.conn.commit()
            logging.info(f"Bulk inserted {len(cr_data)} change requests.")
        except sqlite3.Error as e:
            logging.error(f"Bulk change request insert failed: {e}\nQuery: {query}")
            self.conn.rollback()
            raise

    def add_or_update_artifact(self, artifact_data: dict):
        """
        Creates a new artifact record or replaces an existing one using the primary key.
        """
        if 'artifact_id' not in artifact_data:
            raise ValueError("artifact_data must contain 'artifact_id' for an add_or_update operation.")
        columns = ', '.join(artifact_data.keys())
        placeholders = ', '.join('?' * len(artifact_data))
        query = f"INSERT OR REPLACE INTO Artifacts ({columns}) VALUES ({placeholders})"
        params = tuple(artifact_data.values())
        self._execute_query(query, params)
        logging.info(f"Successfully added or updated artifact with ID '{artifact_data['artifact_id']}'.")

    # --- FactoryConfig CRUD Operations ---

    def set_config_value(self, key: str, value: str, description: Optional[str] = None):
        """
        Saves or updates a configuration setting in the FactoryConfig table.
        """
        query = "INSERT OR REPLACE INTO FactoryConfig (key, value, description) VALUES (?, ?, ?)"
        params = (key, value, description)
        self._execute_query(query, params)
        logging.info(f"Set configuration value for key '{key}'.")

    def get_config_value(self, key: str) -> str | None:
        """
        Retrieves a specific configuration value by its key.
        """
        query = "SELECT value FROM FactoryConfig WHERE key = ?"
        cursor = self._execute_query(query, (key,))
        row = cursor.fetchone()
        if row:
            logging.info(f"Retrieved configuration for key '{key}'.")
            return row[0]
        logging.info(f"No configuration found for key '{key}'.")
        return None

    def get_all_config_values(self) -> dict[str, str]:
        """
        Retrieves all configuration settings from the FactoryConfig table.
        """
        query = "SELECT key, value FROM FactoryConfig"
        cursor = self._execute_query(query)
        return {row[0]: row[1] for row in cursor.fetchall()}

    # --- ProjectHistory CRUD Operations ---

    def add_project_to_history(self, project_id: str, project_name: str, root_folder: str, archive_path: str, timestamp: str):
        """
        Adds a record of a stopped/exported project to the ProjectHistory table.
        """
        query = """
        INSERT INTO ProjectHistory
        (project_id, project_name, project_root_folder, archive_file_path, last_stop_timestamp)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (project_id, project_name, root_folder, archive_path, timestamp)
        self._execute_query(query, params)
        logging.info(f"Added project '{project_name}' to history. Archive at: {archive_path}")

    def get_project_history(self) -> list[sqlite3.Row]:
        """
        Retrieves all records from the ProjectHistory table.
        """
        query = "SELECT * FROM ProjectHistory ORDER BY last_stop_timestamp DESC"
        cursor = self._execute_query(query)
        return cursor.fetchall()

    def get_project_history_by_id(self, history_id: int) -> sqlite3.Row | None:
        """
        Retrieves a single project history record by its primary key.
        """
        query = "SELECT * FROM ProjectHistory WHERE history_id = ?"
        cursor = self._execute_query(query, (history_id,))
        return cursor.fetchone()

    def delete_project_from_history(self, history_id: int):
        """
        Deletes a project record from the ProjectHistory table.
        """
        query = "DELETE FROM ProjectHistory WHERE history_id = ?"
        self._execute_query(query, (history_id,))
        logging.info(f"Deleted project history record with ID '{history_id}'.")

    # --- ChangeRequestRegister CRUD Operations ---

    def get_all_change_requests_for_project(self, project_id: str) -> list:
        """
        Retrieves all change request records for a given project.
        """
        query = "SELECT * FROM ChangeRequestRegister WHERE project_id = ? ORDER BY creation_timestamp DESC"
        cursor = self._execute_query(query, (project_id,))
        change_requests = cursor.fetchall()
        logging.info(f"Retrieved {len(change_requests)} change requests for project ID '{project_id}'.")
        return change_requests

    def get_change_requests_by_statuses(self, project_id: str, statuses: list[str]) -> list:
        """
        Retrieves all change requests for a project that match a list of statuses.
        """
        if not statuses:
            return []
        placeholders = ', '.join('?' for _ in statuses)
        query = f"SELECT * FROM ChangeRequestRegister WHERE project_id = ? AND status IN ({placeholders}) ORDER BY creation_timestamp DESC"
        params = (project_id,) + tuple(statuses)
        cursor = self._execute_query(query, params)
        return cursor.fetchall()

    def add_change_request(self, project_id: str, description: str, request_type: str = 'CHANGE_REQUEST') -> int:
        """
        Adds a new change request to the ChangeRequestRegister table.
        """
        query = """
        INSERT INTO ChangeRequestRegister
        (project_id, description, creation_timestamp, status, request_type)
        VALUES (?, ?, ?, ?, ?)
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        status = "RAISED"
        params = (project_id, description, timestamp, status, request_type)
        cursor = self._execute_query(query, params)
        new_cr_id = cursor.lastrowid
        logging.info(f"Added new change request with ID '{new_cr_id}' for project '{project_id}'.")
        return new_cr_id

    def add_bug_report(self, project_id: str, description: str, severity: str) -> int:
        """
        Adds a new bug report to the ChangeRequestRegister table.
        """
        query = """
        INSERT INTO ChangeRequestRegister
        (project_id, request_type, description, creation_timestamp, status, impact_rating)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        params = (project_id, 'BUG_REPORT', description, timestamp, 'RAISED', severity)
        cursor = self._execute_query(query, params)
        new_bug_id = cursor.lastrowid
        logging.info(f"Added new bug report with ID '{new_bug_id}' for project '{project_id}'.")
        return new_bug_id

    def add_linked_change_request(self, project_id: str, description: str, linked_cr_id: int) -> int:
        """
        Adds a new, auto-generated Change Request that is linked to a parent.
        """
        query = """
        INSERT INTO ChangeRequestRegister
        (project_id, request_type, description, creation_timestamp, status, linked_cr_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        params = (project_id, 'CHANGE_REQUEST', description, timestamp, 'RAISED', linked_cr_id)
        cursor = self._execute_query(query, params)
        new_cr_id = cursor.lastrowid
        logging.info(f"Added new linked change request with ID '{new_cr_id}' for project '{project_id}'.")
        return new_cr_id

    def update_change_request(self, cr_id: int, new_description: str):
        """
        Updates the description of a given change request and resets its impact analysis fields.
        """
        query = """
        UPDATE ChangeRequestRegister
        SET description = ?,
            impact_rating = NULL,
            impact_analysis_details = NULL,
            last_modified_timestamp = ?
        WHERE cr_id = ?
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        params = (new_description, timestamp, cr_id)
        self._execute_query(query, params)
        logging.info(f"Updated change request ID '{cr_id}' and reset its impact analysis.")

    def delete_change_request(self, cr_id: int):
        """
        Deletes a specific change request from the register.
        """
        query = "DELETE FROM ChangeRequestRegister WHERE cr_id = ?"
        params = (cr_id,)
        self._execute_query(query, params)
        logging.info(f"Deleted change request with ID '{cr_id}'.")

    def update_cr_impact_analysis(self, cr_id: int, rating: str, details: str, artifact_ids: list[str]):
        """
        Updates a change request record with the results of an impact analysis.
        """
        ids_json = json.dumps(artifact_ids)
        query = """
        UPDATE ChangeRequestRegister
        SET impact_rating = ?,
            impact_analysis_details = ?,
            impacted_artifact_ids = ?,
            status = 'IMPACT_ANALYZED',
            last_modified_timestamp = ?
        WHERE cr_id = ?
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        params = (rating, details, ids_json, timestamp, cr_id)
        self._execute_query(query, params)
        logging.info(f"Updated CR ID '{cr_id}' with impact analysis results.")

    def update_cr_status(self, cr_id: int, new_status: str):
        """
        Updates the status of a specific change request.
        """
        query = "UPDATE ChangeRequestRegister SET status = ?, last_modified_timestamp = ? WHERE cr_id = ?"
        timestamp = datetime.now(timezone.utc).isoformat()
        params = (new_status, timestamp, cr_id)
        self._execute_query(query, params)
        logging.info(f"Updated status for CR ID '{cr_id}' to '{new_status}'.")

    def get_cr_by_id(self, cr_id: int):
        """
        Retrieves a single change request by its primary key.
        """
        query = "SELECT * FROM ChangeRequestRegister WHERE cr_id = ?"
        cursor = self._execute_query(query, (cr_id,))
        return cursor.fetchone()

    def get_cr_by_linked_id(self, parent_cr_id: int):
        """
        Finds a Change Request that is linked to a specific parent CR.
        """
        query = "SELECT * FROM ChangeRequestRegister WHERE linked_cr_id = ?"
        cursor = self._execute_query(query, (parent_cr_id,))
        return cursor.fetchone()

    def get_cr_by_status(self, project_id: str, status: str) -> sqlite3.Row | None:
        """
        Retrieves the first change request for a project with a specific status.
        """
        query = "SELECT * FROM ChangeRequestRegister WHERE project_id = ? AND status = ? LIMIT 1"
        cursor = self._execute_query(query, (project_id, status))
        return cursor.fetchone()

    # --- OrchestrationState CRUD Operations ---

    def save_orchestration_state(self, project_id: str, current_phase: str, current_step: str, state_details: str, timestamp: str):
        """
        Saves or updates the orchestration state for a given project.
        """
        query = """
        INSERT OR REPLACE INTO OrchestrationState
        (project_id, current_phase, current_step, state_details, last_updated)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (project_id, current_phase, current_step, state_details, timestamp)
        self._execute_query(query, params)
        logging.info(f"Saved orchestration state for project ID '{project_id}'.")

    def get_orchestration_state(self, project_id: str) -> sqlite3.Row | None:
        """
        Retrieves the orchestration state for a given project.
        """
        query = "SELECT * FROM OrchestrationState WHERE project_id = ?"
        cursor = self._execute_query(query, (project_id,))
        return cursor.fetchone()

    def get_any_paused_state(self) -> sqlite3.Row | None:
        """
        Retrieves the first available orchestration state from the database, if any exists.
        This is used to detect if any project is in a paused state on startup.
        """
        query = "SELECT * FROM OrchestrationState LIMIT 1"
        cursor = self._execute_query(query)
        return cursor.fetchone()

    # --- FactoryKnowledgeBase CRUD Operations ---

    def add_kb_entry(self, context: str, problem: str, solution: str, tags: str, timestamp: str):
        """
        Adds a new entry to the FactoryKnowledgeBase.
        """
        query = """
        INSERT INTO FactoryKnowledgeBase (context, problem, solution, tags, creation_timestamp)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (context, problem, solution, tags, timestamp)
        self._execute_query(query, params)
        logging.info(f"Added new entry to Factory Knowledge Base with tags: {tags}")

    def query_kb_by_tags(self, tags: list[str]) -> list[sqlite3.Row]:
        """
        Queries the knowledge base for entries matching one or more tags.
        """
        if not tags:
            return []
        likes = ' OR '.join(['tags LIKE ?' for _ in tags])
        query = f"SELECT * FROM FactoryKnowledgeBase WHERE {likes}"
        params = [f'%{tag}%' for tag in tags]
        cursor = self._execute_query(query, tuple(params))
        return cursor.fetchall()