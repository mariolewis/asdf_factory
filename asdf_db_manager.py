import sqlite3
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

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

        # SQL for creating the Projects table
        create_projects_table = """
        CREATE TABLE IF NOT EXISTS Projects (
            project_id TEXT PRIMARY KEY,
            project_name TEXT NOT NULL,
            creation_timestamp TEXT NOT NULL
        );
        """
        self._execute_query(create_projects_table)

        # SQL for creating the Artifacts (RoWD) table
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

        # SQL for creating the OrchestrationState table
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

        # SQL for creating the FactoryConfig table
        create_factory_config_table = """
        CREATE TABLE IF NOT EXISTS FactoryConfig (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT
        );
        """
        self._execute_query(create_factory_config_table)

        # SQL for creating the FactoryKnowledgeBase table
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

        # SQL for creating the ProjectHistory table
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

    def delete_project_from_history(self, history_id: int):
        """
        Deletes a project record from the ProjectHistory table.

        Args:
            history_id (int): The history_id of the record to delete.
        """
        query = "DELETE FROM ProjectHistory WHERE history_id = ?"
        self._execute_query(query, (history_id,))
        logging.info(f"Deleted project history record with ID '{history_id}'.")

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