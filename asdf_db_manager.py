import sqlite3
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
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
            self.conn = sqlite3.connect(self.db_path)
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

        # CORRECTED: Added the missing CREATE TABLE statement for the Projects table.
        create_projects_table = """
        CREATE TABLE IF NOT EXISTS Projects (
            project_id TEXT PRIMARY KEY,
            project_name TEXT NOT NULL,
            creation_timestamp TEXT NOT NULL,
            technology_stack TEXT,
            project_root_folder TEXT,
            apex_executable_name TEXT,
            final_spec_text TEXT,
            tech_spec_text TEXT,
            is_build_automated BOOLEAN NOT NULL DEFAULT 1,
            coding_standard_text TEXT,
            development_plan_text TEXT,
            integration_plan_text TEXT,
            ui_test_plan_text TEXT
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

        Args:
            project_id (str): The unique identifier for the project.
            project_name (str): The human-readable name of the project.
            creation_timestamp (str): The ISO 8601 timestamp of creation.

        Returns:
            str: The project_id of the newly created project.
        """
        query = "INSERT INTO Projects (project_id, project_name, creation_timestamp) VALUES (?, ?, ?)"
        params = (project_id, project_name, creation_timestamp)
        self._execute_query(query, params)
        logging.info(f"Created new project '{project_name}' with ID '{project_id}'.")
        return project_id

    def get_project_by_id(self, project_id: str) -> sqlite3.Row | None:
        """
        Retrieves a single project record by its ID.

        Args:
            project_id (str): The ID of the project to retrieve.

        Returns:
            sqlite3.Row | None: A Row object representing the project, or None if not found.
        """
        query = "SELECT * FROM Projects WHERE project_id = ?"
        cursor = self._execute_query(query, (project_id,))
        return cursor.fetchone()

    def save_final_specification(self, project_id: str, spec_text: str):
        """
        Saves the finalized specification text to the project's record.

        Args:
            project_id (str): The ID of the project to update.
            spec_text (str): The final, approved specification text.
        """
        query = "UPDATE Projects SET final_spec_text = ? WHERE project_id = ?"
        params = (spec_text, project_id)
        self._execute_query(query, params)
        logging.info(f"Saved final specification for project ID '{project_id}'.")

    def save_tech_specification(self, project_id: str, tech_spec_text: str):
        """
        Saves the formal Technical Specification Document text to the project's record.
        (ASDF Change Request CR-ASDF-001)

        Args:
            project_id (str): The ID of the project to update.
            tech_spec_text (str): The final, approved technical specification text.
        """
        query = "UPDATE Projects SET tech_spec_text = ? WHERE project_id = ?"
        params = (tech_spec_text, project_id)
        self._execute_query(query, params)
        logging.info(f"Saved technical specification for project ID '{project_id}'.")

    def save_coding_standard(self, project_id: str, standard_text: str):
        """
        Saves the approved Coding Standard text to the project's record.

        Args:
            project_id (str): The ID of the project to update.
            standard_text (str): The final, approved coding standard text.
        """
        query = "UPDATE Projects SET coding_standard_text = ? WHERE project_id = ?"
        params = (standard_text, project_id)
        self._execute_query(query, params)
        logging.info(f"Saved coding standard for project ID '{project_id}'.")

    def save_development_plan(self, project_id: str, plan_text: str):
        """
        Saves the approved Development Plan text to the project's record.

        Args:
            project_id (str): The ID of the project to update.
            plan_text (str): The final, approved development plan JSON string.
        """
        query = "UPDATE Projects SET development_plan_text = ? WHERE project_id = ?"
        params = (plan_text, project_id)
        self._execute_query(query, params)
        logging.info(f"Saved development plan for project ID '{project_id}'.")

    def save_integration_plan(self, project_id: str, plan_text: str):
        """
        Saves the generated Integration Plan text to the project's record.

        Args:
            project_id (str): The ID of the project to update.
            plan_text (str): The integration plan JSON string.
        """
        query = "UPDATE Projects SET integration_plan_text = ? WHERE project_id = ?"
        params = (plan_text, project_id)
        self._execute_query(query, params)
        logging.info(f"Saved integration plan for project ID '{project_id}'.")

    def save_ui_test_plan(self, project_id: str, plan_text: str):
        """
        Saves the generated UI Test Plan text to the project's record.

        Args:
            project_id (str): The ID of the project to update.
            plan_text (str): The UI test plan markdown string.
        """
        query = "UPDATE Projects SET ui_test_plan_text = ? WHERE project_id = ?"
        params = (plan_text, project_id)
        self._execute_query(query, params)
        logging.info(f"Saved UI test plan for project ID '{project_id}'.")

    def update_project_technology(self, project_id: str, technology_stack: str):
        """
        Updates the technology_stack for a given project.

        Args:
            project_id (str): The ID of the project to update.
            technology_stack (str): The name of the technology (e.g., 'Python', 'Kotlin').
        """
        query = "UPDATE Projects SET technology_stack = ? WHERE project_id = ?"
        params = (technology_stack, project_id)
        self._execute_query(query, params)
        logging.info(f"Set technology stack for project ID '{project_id}' to '{technology_stack}'.")

    def update_project_apex_file(self, project_id: str, apex_name: str):
        """
        Updates the apex_executable_name for a given project.

        Args:
            project_id (str): The ID of the project to update.
            apex_name (str): The name of the apex executable file (without extension).
        """
        query = "UPDATE Projects SET apex_executable_name = ? WHERE project_id = ?"
        params = (apex_name, project_id)
        self._execute_query(query, params)
        logging.info(f"Set apex file for project ID '{project_id}' to '{apex_name}'.")

    def update_project_build_automation_status(self, project_id: str, is_automated: bool):
        """
        Updates the build automation status for a given project.

        Args:
            project_id (str): The ID of the project to update.
            is_automated (bool): True if ASDF should manage the build, False otherwise.
        """
        # SQLite uses 1 for True and 0 for False
        status_as_int = 1 if is_automated else 0
        query = "UPDATE Projects SET is_build_automated = ? WHERE project_id = ?"
        params = (status_as_int, project_id)
        self._execute_query(query, params)
        logging.info(f"Set build automation status for project ID '{project_id}' to {is_automated}.")

    # --- Artifact (RoWD) CRUD Operations ---

    def create_artifact(self, artifact: Artifact):
        """
        Creates a new artifact record in the Artifacts table from an Artifact object.

        Args:
            artifact (Artifact): The dataclass object containing all artifact data.
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

        Args:
            artifact_id (str): The ID of the artifact to retrieve.

        Returns:
            sqlite3.Row | None: A Row object representing the artifact, or None if not found.
        """
        query = "SELECT * FROM Artifacts WHERE artifact_id = ?"
        cursor = self._execute_query(query, (artifact_id,))
        return cursor.fetchone()

    def update_artifact_status(self, artifact_id: str, status: str, timestamp: str):
        """
        Updates the status and timestamp of a specific artifact.

        Args:
            artifact_id (str): The ID of the artifact to update.
            status (str): The new status for the artifact.
            timestamp (str): The ISO 8601 timestamp of the update.
        """
        query = "UPDATE Artifacts SET status = ?, last_modified_timestamp = ? WHERE artifact_id = ?"
        params = (status, timestamp, artifact_id)
        self._execute_query(query, params)
        logging.info(f"Updated status for artifact ID '{artifact_id}' to '{status}'.")

    def get_component_counts_by_status(self, project_id: str) -> dict[str, int]:
        """
        Gets the count of artifacts for each status for a given project.
        This supports the "Development Progress Summary" report.

        Args:
            project_id (str): The ID of the project.

        Returns:
            dict[str, int]: A dictionary mapping each status to its count.
        """
        query = "SELECT status, COUNT(*) FROM Artifacts WHERE project_id = ? GROUP BY status"
        cursor = self._execute_query(query, (project_id,))

        status_counts = {row[0]: row[1] for row in cursor.fetchall()}
        logging.info(f"Retrieved component counts for project ID '{project_id}': {status_counts}")
        return status_counts

    def get_artifacts_by_statuses(self, project_id: str, statuses: list[str]) -> list[sqlite3.Row]:
        """
        Retrieves all artifacts for a project that match a list of statuses.
        This supports the "Pending Changes & Bug Fix Status" report.

        Args:
            project_id (str): The ID of the project.
            statuses (list[str]): A list of statuses to filter by.

        Returns:
            list[sqlite3.Row]: A list of Row objects representing the matching artifacts.
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
        This supports the "Development Progress Summary" report.

        Args:
            project_id (str): The ID of the project.

        Returns:
            list[sqlite3.Row]: A list of Row objects for all artifacts in the project.
        """
        query = "SELECT * FROM Artifacts WHERE project_id = ? ORDER BY artifact_name"
        cursor = self._execute_query(query, (project_id,))
        return cursor.fetchall()

    def delete_all_artifacts_for_project(self, project_id: str):
        """
        Deletes all artifact records for a given project from the Artifacts table.

        Args:
            project_id (str): The ID of the project whose artifacts should be deleted.
        """
        query = "DELETE FROM Artifacts WHERE project_id = ?"
        self._execute_query(query, (project_id,))
        logging.info(f"Deleted all RoWD artifacts for project ID '{project_id}'.")

    def delete_all_change_requests_for_project(self, project_id: str):
        """
        Deletes all change requests for a given project.

        Args:
            project_id (str): The ID of the project whose CRs should be deleted.
        """
        query = "DELETE FROM ChangeRequestRegister WHERE project_id = ?"
        self._execute_query(query, (project_id,))
        logging.info(f"Deleted all Change Requests for project ID '{project_id}'.")

    def delete_orchestration_state_for_project(self, project_id: str):
        """
        Deletes the orchestration state record for a given project.

        Args:
            project_id (str): The ID of the project whose state should be deleted.
        """
        query = "DELETE FROM OrchestrationState WHERE project_id = ?"
        self._execute_query(query, (project_id,))
        logging.info(f"Deleted Orchestration State for project ID '{project_id}'.")

    def bulk_insert_artifacts(self, artifacts_data: list[dict]):
        """
        Inserts multiple artifact records into the database.
        This is used when loading an archived project.

        Args:
            artifacts_data (list[dict]): A list of dictionaries, where each
                                         dictionary represents an artifact's data.
        """
        if not artifacts_data:
            return

        # Assumes all dicts have the same keys as the first one
        columns = ', '.join(artifacts_data[0].keys())
        placeholders = ', '.join('?' for _ in artifacts_data[0])
        query = f"INSERT INTO Artifacts ({columns}) VALUES ({placeholders})"

        # Create a list of tuples from the list of dicts
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
        This is used when loading an archived project.

        Args:
            cr_data (list[dict]): A list of dictionaries, where each
                                   dictionary represents a change request's data.
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
        This effectively handles both INSERT and UPDATE operations (UPSERT).

        Args:
            artifact_data (dict): A dictionary of the artifact's data.
                                  It MUST include the 'artifact_id' primary key.
        """
        if 'artifact_id' not in artifact_data:
            raise ValueError("artifact_data must contain 'artifact_id' for an add_or_update operation.")

        # This uses the dictionary keys for columns and question marks for placeholders
        columns = ', '.join(artifact_data.keys())
        placeholders = ', '.join('?' * len(artifact_data))

        # INSERT OR REPLACE is a SQLite-specific command that simplifies UPSERT logic.
        query = f"INSERT OR REPLACE INTO Artifacts ({columns}) VALUES ({placeholders})"

        params = tuple(artifact_data.values())
        self._execute_query(query, params)
        logging.info(f"Successfully added or updated artifact with ID '{artifact_data['artifact_id']}'.")

    # --- FactoryConfig CRUD Operations ---

    def set_config_value(self, key: str, value: str):
        """
        Saves or updates a configuration setting in the FactoryConfig table.
        It uses INSERT OR REPLACE to handle both new and existing keys.

        Args:
            key (str): The configuration key (e.g., 'GEMINI_API_KEY').
            value (str): The value to store for the key.
        """
        query = "INSERT OR REPLACE INTO FactoryConfig (key, value) VALUES (?, ?)"
        params = (key, value)
        self._execute_query(query, params)
        logging.info(f"Set configuration value for key '{key}'.")

    def get_config_value(self, key: str) -> str | None:
        """
        Retrieves a specific configuration value by its key.

        Args:
            key (str): The configuration key to retrieve.

        Returns:
            str | None: The value of the setting, or None if the key is not found.
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

        Returns:
            dict[str, str]: A dictionary of all key-value pairs.
        """
        query = "SELECT key, value FROM FactoryConfig"
        cursor = self._execute_query(query)
        return {row[0]: row[1] for row in cursor.fetchall()}

    # --- ProjectHistory CRUD Operations ---

    def add_project_to_history(self, project_id: str, project_name: str, root_folder: str, archive_path: str, timestamp: str):
        """
        Adds a record of a stopped/exported project to the ProjectHistory table.

        Args:
            project_id (str): The unique project identifier.
            project_name (str): The human-readable project name.
            root_folder (str): The local file system path for the project's root.
            archive_path (str): The full path to the exported archive file.
            timestamp (str): The ISO 8601 timestamp of when the project was stopped.
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

        Returns:
            list[sqlite3.Row]: A list of Row objects, each representing an archived project.
        """
        query = "SELECT * FROM ProjectHistory ORDER BY last_stop_timestamp DESC"
        cursor = self._execute_query(query)
        return cursor.fetchall()

    def get_project_history_by_id(self, history_id: int) -> sqlite3.Row | None:
        """
        Retrieves a single project history record by its primary key.

        Args:
            history_id (int): The history_id of the record to retrieve.

        Returns:
            sqlite3.Row | None: A Row object representing the history record, or None if not found.
        """
        query = "SELECT * FROM ProjectHistory WHERE history_id = ?"
        cursor = self._execute_query(query, (history_id,))
        return cursor.fetchone()

    def delete_project_from_history(self, history_id: int):
        """
        Deletes a project record from the ProjectHistory table.

        Args:
            history_id (int): The history_id of the record to delete.
        """
        query = "DELETE FROM ProjectHistory WHERE history_id = ?"
        self._execute_query(query, (history_id,))
        logging.info(f"Deleted project history record with ID '{history_id}'.")

    # --- ChangeRequestRegister CRUD Operations ---

    def get_all_change_requests_for_project(self, project_id: str) -> list:
        """
        Retrieves all change request records for a given project.

        Args:
            project_id (str): The ID of the project.

        Returns:
            list: A list of row objects representing all change requests for the project,
                  ordered by the most recent first.
        """
        query = "SELECT * FROM ChangeRequestRegister WHERE project_id = ? ORDER BY creation_timestamp DESC"
        cursor = self._execute_query(query, (project_id,))
        change_requests = cursor.fetchall()
        logging.info(f"Retrieved {len(change_requests)} change requests for project ID '{project_id}'.")
        return change_requests

    def get_change_requests_by_statuses(self, project_id: str, statuses: list[str]) -> list:
        """
        Retrieves all change requests for a project that match a list of statuses.

        Args:
            project_id (str): The ID of the project.
            statuses (list[str]): A list of statuses to filter by.

        Returns:
            list: A list of row objects representing the matching change requests.
        """
        if not statuses:
            return []

        placeholders = ', '.join('?' for _ in statuses)
        query = f"SELECT * FROM ChangeRequestRegister WHERE project_id = ? AND status IN ({placeholders}) ORDER BY creation_timestamp DESC"
        params = (project_id,) + tuple(statuses)
        cursor = self._execute_query(query, params)
        return cursor.fetchall()

    def add_change_request(self, project_id: str, description: str) -> int:
        """
        Adds a new change request to the ChangeRequestRegister table.

        Args:
            project_id (str): The ID of the project this change request belongs to.
            description (str): The PM's description of the requested change.

        Returns:
            int: The ID (primary key) of the newly created change request record.
        """
        query = """
        INSERT INTO ChangeRequestRegister
        (project_id, description, creation_timestamp, status)
        VALUES (?, ?, ?, ?)
        """
        # CORRECTED: Using timezone-aware datetime
        timestamp = datetime.now(timezone.utc).isoformat()
        status = "RAISED" # Initial status for any new change request
        params = (project_id, description, timestamp, status)

        cursor = self._execute_query(query, params)
        new_cr_id = cursor.lastrowid
        logging.info(f"Added new change request with ID '{new_cr_id}' for project '{project_id}'.")
        return new_cr_id

    def add_bug_report(self, project_id: str, description: str, severity: str) -> int:
        """
        Adds a new bug report to the ChangeRequestRegister table.

        Args:
            project_id (str): The ID of the project the bug belongs to.
            description (str): The PM's description of the bug.
            severity (str): The PM-assigned severity ('Minor', 'Medium', 'Major').

        Returns:
            int: The ID (primary key) of the newly created bug report record.
        """
        query = """
        INSERT INTO ChangeRequestRegister
        (project_id, request_type, description, creation_timestamp, status, impact_rating)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        # Set the type to 'BUG_REPORT' and status to 'RAISED'
        params = (project_id, 'BUG_REPORT', description, timestamp, 'RAISED', severity)

        cursor = self._execute_query(query, params)
        new_bug_id = cursor.lastrowid
        logging.info(f"Added new bug report with ID '{new_bug_id}' for project '{project_id}'.")
        return new_bug_id

    def add_linked_change_request(self, project_id: str, description: str, linked_cr_id: int) -> int:
        """
        Adds a new, auto-generated Change Request that is linked to a
        parent (e.g., a Specification Correction CR).

        Args:
            project_id (str): The ID of the project.
            description (str): The auto-generated description for the new CR.
            linked_cr_id (int): The ID of the parent CR this new CR is linked to.

        Returns:
            int: The ID of the newly created CR.
        """
        query = """
        INSERT INTO ChangeRequestRegister
        (project_id, request_type, description, creation_timestamp, status, linked_cr_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        # This auto-generated CR starts in the 'RAISED' state.
        params = (project_id, 'CHANGE_REQUEST', description, timestamp, 'RAISED', linked_cr_id)

        cursor = self._execute_query(query, params)
        new_cr_id = cursor.lastrowid
        logging.info(f"Added new linked change request with ID '{new_cr_id}' for project '{project_id}'.")
        return new_cr_id

    def update_change_request(self, cr_id: int, new_description: str):
        """
        Updates the description of a given change request and resets its
        impact analysis fields.
        """
        query = """
        UPDATE ChangeRequestRegister
        SET description = ?,
            impact_rating = NULL,
            impact_analysis_details = NULL,
            last_modified_timestamp = ?
        WHERE cr_id = ?
        """
        # CORRECTED: Using timezone-aware UTC time
        timestamp = datetime.now(timezone.utc).isoformat()
        params = (new_description, timestamp, cr_id)
        self._execute_query(query, params)
        logging.info(f"Updated change request ID '{cr_id}' and reset its impact analysis.")

    def delete_change_request(self, cr_id: int):
        """
        Deletes a specific change request from the register.

        The business logic layer (e.g., MasterOrchestrator) is responsible
        for ensuring this is only called on CRs with a 'RAISED' status.

        Args:
            cr_id (int): The ID of the change request to delete.
        """
        query = "DELETE FROM ChangeRequestRegister WHERE cr_id = ?"
        params = (cr_id,)
        self._execute_query(query, params)
        logging.info(f"Deleted change request with ID '{cr_id}'.")

    def update_cr_impact_analysis(self, cr_id: int, rating: str, details: str, artifact_ids: list[str]):
        """
        Updates a change request record with the results of an impact analysis.
        """
        # Convert the list of artifact IDs to a JSON string for storage
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

        Args:
            cr_id (int): The ID of the change request to update.
            new_status (str): The new status to set.
        """
        query = "UPDATE ChangeRequestRegister SET status = ?, last_modified_timestamp = ? WHERE cr_id = ?"
        # CORRECTED: Using timezone-aware datetime
        timestamp = datetime.now(timezone.utc).isoformat()
        params = (new_status, timestamp, cr_id)
        self._execute_query(query, params)
        logging.info(f"Updated status for CR ID '{cr_id}' to '{new_status}'.")

    def get_cr_by_id(self, cr_id: int):
        """
        Retrieves a single change request by its primary key.

        Args:
            cr_id (int): The ID of the change request to retrieve.

        Returns:
            A row object representing the change request, or None if not found.
        """
        query = "SELECT * FROM ChangeRequestRegister WHERE cr_id = ?"
        cursor = self._execute_query(query, (cr_id,))
        return cursor.fetchone()

    def get_cr_by_linked_id(self, parent_cr_id: int):
        """
        Finds a Change Request that is linked to a specific parent CR.

        Args:
            parent_cr_id (int): The ID of the parent CR to find the child for.

        Returns:
            A row object representing the linked child CR, or None if not found.
        """
        query = "SELECT * FROM ChangeRequestRegister WHERE linked_cr_id = ?"
        cursor = self._execute_query(query, (parent_cr_id,))
        return cursor.fetchone()

    def get_cr_by_status(self, project_id: str, status: str) -> sqlite3.Row | None:
        """
        Retrieves the first change request for a project with a specific status.

        Args:
            project_id (str): The ID of the project.
            status (str): The status to filter by.

        Returns:
            sqlite3.Row | None: A Row object representing the CR, or None if not found.
        """
        query = "SELECT * FROM ChangeRequestRegister WHERE project_id = ? AND status = ? LIMIT 1"
        cursor = self._execute_query(query, (project_id, status))
        return cursor.fetchone()

    # --- OrchestrationState CRUD Operations ---

    def save_orchestration_state(self, project_id: str, current_phase: str, current_step: str, state_details: str, timestamp: str):
        """
        Saves or updates the orchestration state for a given project.
        Uses INSERT OR REPLACE to ensure only one state record exists per project.

        Args:
            project_id (str): The ID of the project whose state is being saved.
            current_phase (str): The F-Phase the orchestrator is currently in.
            current_step (str): The specific step within the phase.
            state_details (str): A JSON string containing any detailed state information.
            timestamp (str): The ISO 8601 timestamp of the save.
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

        Args:
            project_id (str): The ID of the project.

        Returns:
            sqlite3.Row | None: A Row object representing the state, or None if not found.
        """
        query = "SELECT * FROM OrchestrationState WHERE project_id = ?"
        cursor = self._execute_query(query, (project_id,))
        return cursor.fetchone()

    # --- FactoryKnowledgeBase CRUD Operations ---

    def add_kb_entry(self, context: str, problem: str, solution: str, tags: str, timestamp: str):
        """
        Adds a new entry to the FactoryKnowledgeBase.

        Args:
            context (str): The context in which the problem occurred.
            problem (str): A description of the problem encountered.
            solution (str): The successful solution that was applied.
            tags (str): Comma-separated tags for easy searching.
            timestamp (str): The ISO 8601 timestamp of the entry.
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

        Args:
            tags (list[str]): A list of tags to search for.

        Returns:
            list[sqlite3.Row]: A list of matching knowledge base entries.
        """
        if not tags:
            return []

        # Creates a query like: SELECT * FROM FactoryKnowledgeBase WHERE tags LIKE ? OR tags LIKE ? ...
        likes = ' OR '.join(['tags LIKE ?' for _ in tags])
        query = f"SELECT * FROM FactoryKnowledgeBase WHERE {likes}"

        # Params need to have '%' wildcards for the LIKE search
        params = [f'%{tag}%' for tag in tags]

        cursor = self._execute_query(query, tuple(params))
        return cursor.fetchall()