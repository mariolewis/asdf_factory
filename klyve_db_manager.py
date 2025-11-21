import sqlite3
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List
import json
import uuid
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

class KlyveDBManager:
    """
    Data Access Object (DAO) for the Klyve SQLite database.
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
            db_schema_spec_text TEXT,
            is_build_automated BOOLEAN NOT NULL DEFAULT 1, build_script_file_name TEXT,
            development_plan_text TEXT, integration_plan_text TEXT,
            ui_test_plan_text TEXT, test_execution_command TEXT, ui_test_execution_command TEXT,
            integration_test_command TEXT, integration_settings TEXT,
            version_control_enabled BOOLEAN NOT NULL DEFAULT 0,
            is_backlog_generated BOOLEAN NOT NULL DEFAULT 0,
            detected_technologies TEXT,
            scanned_file_count INTEGER DEFAULT 0
        );"""
        self._execute_query(create_projects_table)

        create_sprints_table = """
        CREATE TABLE IF NOT EXISTS Sprints (
            sprint_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            start_timestamp TEXT NOT NULL,
            end_timestamp TEXT,
            status TEXT NOT NULL,
            sprint_goal TEXT,
            sprint_plan_json TEXT,
            FOREIGN KEY (project_id) REFERENCES Projects (project_id)
        );"""
        self._execute_query(create_sprints_table)

        create_doc_review_log_table = """
        CREATE TABLE IF NOT EXISTS DocumentReviewLog (
            log_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            document_path TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            author TEXT NOT NULL,
            log_text TEXT,
            status TEXT,
            FOREIGN KEY (project_id) REFERENCES Projects (project_id)
        );"""
        self._execute_query(create_doc_review_log_table)

        create_sprint_items_table = """
        CREATE TABLE IF NOT EXISTS SprintItems (
            sprint_id TEXT NOT NULL,
            cr_id INTEGER NOT NULL,
            PRIMARY KEY (sprint_id, cr_id),
            FOREIGN KEY (sprint_id) REFERENCES Sprints (sprint_id),
            FOREIGN KEY (cr_id) REFERENCES ChangeRequestRegister (cr_id)
        );"""
        self._execute_query(create_sprint_items_table)

        create_cr_register_table = """
        CREATE TABLE IF NOT EXISTS ChangeRequestRegister (
            cr_id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL,
            title TEXT,
            request_type TEXT NOT NULL DEFAULT 'BACKLOG_ITEM', description TEXT NOT NULL,
            creation_timestamp TEXT NOT NULL, last_modified_timestamp TEXT, status TEXT NOT NULL,
            impact_rating TEXT, impact_analysis_details TEXT, impacted_artifact_ids TEXT, technical_preview_text TEXT,
            display_order INTEGER NOT NULL DEFAULT 0,
            priority TEXT,
            complexity TEXT,
            external_id TEXT UNIQUE,
            external_url TEXT,
            linked_cr_id INTEGER,
            parent_cr_id INTEGER,
            FOREIGN KEY (parent_cr_id) REFERENCES ChangeRequestRegister (cr_id),
            FOREIGN KEY (project_id) REFERENCES Projects (project_id),
            FOREIGN KEY (linked_cr_id) REFERENCES ChangeRequestRegister (cr_id)
        );"""
        self._execute_query(create_cr_register_table)

        create_artifacts_table = """
        CREATE TABLE IF NOT EXISTS Artifacts (
            artifact_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            status TEXT,
            file_path TEXT,
            artifact_name TEXT NOT NULL,
            artifact_type TEXT NOT NULL,
            signature TEXT,
            short_description TEXT,
            version INTEGER NOT NULL DEFAULT 1,
            last_modified_timestamp TEXT NOT NULL,
            commit_hash TEXT,
            file_hash TEXT,
            micro_spec_id TEXT,
            dependencies TEXT,
            unit_test_status TEXT,
            code_summary TEXT,
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

    def create_project(self, project_id: str, project_name: str, project_root: str, creation_timestamp: str) -> str:
        self._execute_query("INSERT INTO Projects (project_id, project_name, project_root_folder, creation_timestamp) VALUES (?, ?, ?, ?)", (project_id, project_name, project_root, creation_timestamp))
        return project_id

    def get_project_by_id(self, project_id: str) -> Optional[sqlite3.Row]:
        return self._execute_query("SELECT * FROM Projects WHERE project_id = ?", (project_id,), fetch="one")

    def get_all_active_projects(self) -> list:
        """Retrieves all project records from the Projects table."""
        return self._execute_query("SELECT * FROM Projects ORDER BY creation_timestamp DESC", fetch="all")

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

    def get_artifact_by_path(self, project_id: str, file_path: str) -> Optional[sqlite3.Row]:
        """Retrieves a single artifact record by its unique file path for a given project."""
        return self._execute_query(
            "SELECT * FROM Artifacts WHERE project_id = ? AND file_path = ?",
            (project_id, file_path),
            fetch="one"
        )

    def get_artifacts_by_micro_spec_ids(self, project_id: str, micro_spec_ids: list[str]) -> list:
        """
        Retrieves all artifacts for a project matching any of the provided micro_spec_ids.

        Args:
            project_id (str): The ID of the project.
            micro_spec_ids (list[str]): A list of micro_spec_id strings to search for.

        Returns:
            A list of artifact records (as sqlite3.Row objects). Returns empty list on error
            or if no matches are found.
        """
        logging.debug(f"Fetching artifacts by micro_spec_ids for project {project_id}")
        if not micro_spec_ids:
            logging.debug("No micro_spec_ids provided, returning empty list.")
            return []

        try:
            # Create the correct number of placeholders for the IN clause
            placeholders = ', '.join('?' * len(micro_spec_ids))
            query = f"SELECT * FROM Artifacts WHERE project_id = ? AND micro_spec_id IN ({placeholders})"

            # Combine project_id with the list of micro_spec_ids for parameters
            params = (project_id,) + tuple(micro_spec_ids)

            logging.debug(f"Executing query: {query} with {len(params)} params")
            results = self._execute_query(query, params, fetch="all")
            logging.debug(f"Found {len(results)} artifacts matching micro_spec_ids.")
            return results
        except Exception as e:
            logging.error(f"Failed to retrieve artifacts by micro_spec_ids for project {project_id}: {e}", exc_info=True)
            return [] # Return empty list on error

    def get_backlog_status_summary(self, project_id: str) -> dict:
        """
        Counts backlog items (excluding Epics/Features) grouped by status.
        """
        query = """
        SELECT status, COUNT(*) as count
        FROM ChangeRequestRegister
        WHERE project_id = ? AND request_type NOT IN ('Epic', 'Feature') AND status IS NOT NULL AND status != ''
        GROUP BY status;
        """
        rows = self._execute_query(query, (project_id,), fetch="all")
        return {row['status']: row['count'] for row in rows}

    def get_component_test_status_summary(self, project_id: str) -> dict:
        """
        Counts code components (from Artifacts) grouped by unit_test_status.
        """
        query = """
        SELECT unit_test_status, COUNT(*) as count
        FROM Artifacts
        WHERE project_id = ? AND artifact_type = 'code' AND unit_test_status IS NOT NULL
        GROUP BY unit_test_status;
        """
        rows = self._execute_query(query, (project_id,), fetch="all")
        return {row['unit_test_status']: row['count'] for row in rows}

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

    def add_brownfield_artifact(self, artifact_data: dict):
        """
        Dedicated method for adding an artifact from the brownfield scanning process.
        Ensures all mandatory fields including status and timestamp are present.
        """
        # Define all columns the brownfield process is expected to provide
        required_cols = [
            'artifact_id', 'project_id', 'file_path', 'artifact_name',
            'artifact_type', 'code_summary', 'file_hash', 'status',
            'last_modified_timestamp'
        ]

        # Verify that the input data contains all the required columns
        if not all(col in artifact_data for col in required_cols):
            missing = [col for col in required_cols if col not in artifact_data]
            raise ValueError(f"Missing required fields for brownfield artifact: {', '.join(missing)}")

        placeholders = ', '.join(['?'] * len(required_cols))
        cols_str = ', '.join(required_cols)

        query = f"INSERT OR REPLACE INTO Artifacts ({cols_str}) VALUES ({placeholders})"

        # Extract values in the correct, guaranteed order
        values = [artifact_data[col] for col in required_cols]

        try:
            self._execute_query(query, tuple(values))
            logging.info(f"Successfully added brownfield artifact: {artifact_data.get('artifact_id')}")
        except sqlite3.Error as e:
            logging.error(f"Database query failed for brownfield artifact: {e}\nQuery: {query}")
            raise e

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
        return self._execute_query("SELECT * FROM ChangeRequestRegister WHERE project_id = ? ORDER BY display_order ASC", (project_id,), fetch="all")

    def get_top_level_items_for_project(self, project_id: str) -> list:
        """Retrieves all top-level items (those without a parent) for a project."""
        return self._execute_query(
            "SELECT * FROM ChangeRequestRegister WHERE project_id = ? AND parent_cr_id IS NULL ORDER BY display_order ASC",
            (project_id,),
            fetch="all"
        )

    def get_features_for_epic(self, project_id: str, epic_id: int) -> list:
        """Retrieves all FEATURE items linked to a specific EPIC."""
        return self._execute_query(
            "SELECT * FROM ChangeRequestRegister WHERE project_id = ? AND request_type = 'FEATURE' AND parent_cr_id = ? ORDER BY display_order ASC",
            (project_id, epic_id),
            fetch="all"
        )

    def get_items_for_feature(self, project_id: str, feature_id: int) -> list:
        """Retrieves all BACKLOG_ITEM and BUG_REPORT items linked to a specific FEATURE."""
        return self._execute_query(
            "SELECT * FROM ChangeRequestRegister WHERE project_id = ? AND request_type IN ('BACKLOG_ITEM', 'BUG_REPORT') AND parent_cr_id = ? ORDER BY display_order ASC",
            (project_id, feature_id),
            fetch="all"
        )

    def get_children_of_cr(self, parent_cr_id: int) -> list:
        """Retrieves all direct children of a given parent CR item."""
        return self._execute_query(
            "SELECT * FROM ChangeRequestRegister WHERE parent_cr_id = ?",
            (parent_cr_id,),
            fetch="all"
        )

    def update_cr_type(self, cr_id: int, new_type: str):
        """
        Updates the request_type of a single change request item.
        """
        sql = """
        UPDATE ChangeRequestRegister
        SET request_type = ?
        WHERE cr_id = ?
        """
        try:
            # Use _execute_query directly as it handles commit for updates
            self._execute_query(sql, (new_type, cr_id))
            logging.info(f"Updated cr_id {cr_id} to new type {new_type}")
        except sqlite3.Error as e:
            logging.error(f"Failed to update request_type for cr_id {cr_id}: {e}")
            raise

    def update_child_types(self, parent_cr_id: int, new_child_type: str):
        """
        Updates the request_type of all direct children of a given parent CR.
        """
        sql = """
        UPDATE ChangeRequestRegister
        SET request_type = ?
        WHERE parent_cr_id = ?
        """
        try:
            # Use _execute_query directly
            self._execute_query(sql, (new_child_type, parent_cr_id))
            logging.info(f"Updated children of parent_cr_id {parent_cr_id} to new type {new_child_type}")
        except sqlite3.Error as e:
            logging.error(f"Failed to update child request_types for parent_cr_id {parent_cr_id}: {e}")
            raise

    def add_change_request(self, project_id: str, title: str, description: str, request_type: str = 'BACKLOG_ITEM', status: str = 'CHANGE_REQUEST', external_id: str = None, priority: str = None, complexity: str = None, parent_cr_id: int = None, impact_rating: str = None) -> int:
        timestamp = datetime.now(timezone.utc).isoformat()
        max_order_row = self._execute_query("SELECT MAX(display_order) FROM ChangeRequestRegister WHERE project_id = ?", (project_id,), fetch="one")
        new_order = (max_order_row[0] or 0) + 1 if max_order_row else 1

        cursor = self._execute_query(
            "INSERT INTO ChangeRequestRegister (project_id, title, description, creation_timestamp, status, request_type, display_order, external_id, priority, complexity, parent_cr_id, impact_rating) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (project_id, title, description, timestamp, status, request_type, new_order, external_id, priority, complexity, parent_cr_id, impact_rating)
        )
        return cursor.lastrowid

    def add_brownfield_change_request(self, cr_data: dict) -> int:
        """
        Adds a change request from a dictionary. This version is robust and
        dynamically builds the query based on the provided data keys.
        It correctly maps the logical 'cr_id' from the brownfield process
        to the 'external_id' database column and returns the new integer cr_id.
        """
        # Map the logical ID from brownfield scan to the correct DB column.
        if 'cr_id' in cr_data:
            cr_data['external_id'] = cr_data.pop('cr_id')

        if 'project_id' not in cr_data:
            raise ValueError("cr_data for a brownfield item must contain 'project_id'.")

        # Dynamically build the query from the keys in the provided dictionary.
        columns = ', '.join(cr_data.keys())
        placeholders = ', '.join('?' * len(cr_data))
        query = f"INSERT INTO ChangeRequestRegister ({columns}) VALUES ({placeholders})"

        try:
            cursor = self._execute_query(query, tuple(cr_data.values()))
            logging.info(f"Successfully added brownfield change request with external_id: {cr_data.get('external_id')}")
            return cursor.lastrowid
        except sqlite3.Error as e:
            logging.error(f"Database query failed for brownfield CR: {e}")
            raise e

    def add_bug_report(self, project_id: str, description: str, severity: str, complexity: str = None) -> int:
        timestamp = datetime.now(timezone.utc).isoformat()
        max_order_row = self._execute_query("SELECT MAX(display_order) FROM ChangeRequestRegister WHERE project_id = ?", (project_id,), fetch="one")
        new_order = (max_order_row[0] or 0) + 1 if max_order_row else 1

        # Generate a title for the bug report from the description
        title = f"Bug: {description[:50]}" + ("..." if len(description) > 50 else "")

        cursor = self._execute_query(
            "INSERT INTO ChangeRequestRegister (project_id, title, request_type, description, creation_timestamp, status, impact_rating, display_order, complexity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (project_id, title, 'BUG_REPORT', description, timestamp, 'RAISED', severity, new_order, complexity)
        )
        return cursor.lastrowid

    def delete_all_change_requests_for_project(self, project_id: str):
        self._execute_query("DELETE FROM ChangeRequestRegister WHERE project_id = ?", (project_id,))

    def delete_change_requests_by_status(self, project_id: str, statuses: list[str]):
        """
        Deletes all ChangeRequestRegister records for a project that match a
        given list of statuses.
        """
        if not statuses:
            return
        placeholders = ', '.join('?' for _ in statuses)
        query = f"DELETE FROM ChangeRequestRegister WHERE project_id = ? AND status IN ({placeholders})"
        params = (project_id,) + tuple(statuses)
        try:
            self._execute_query(query, params)
            logging.info(f"Deleted CRs with statuses {statuses} for project {project_id}.")
        except sqlite3.Error as e:
            logging.error(f"Failed to delete CRs by status: {e}")
            raise

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

    def get_cr_by_external_id(self, project_id: str, external_id: str):
        """Retrieves a CR by its unique external tool ID to prevent duplicates."""
        return self._execute_query(
            "SELECT * FROM ChangeRequestRegister WHERE project_id = ? AND external_id = ?",
            (project_id, external_id),
            fetch="one"
        )

    def create_sprint(self, project_id: str, sprint_id: str, plan_json: str, sprint_goal: str):
        """Creates a new record for a sprint."""
        timestamp = datetime.now(timezone.utc).isoformat()
        query = "INSERT INTO Sprints (sprint_id, project_id, start_timestamp, status, sprint_plan_json, sprint_goal) VALUES (?, ?, ?, ?, ?, ?)"
        self._execute_query(query, (sprint_id, project_id, timestamp, 'IN_PROGRESS', plan_json, sprint_goal))

    def link_items_to_sprint(self, sprint_id: str, cr_ids: list[int]):
        """Creates records in the SprintItems link table."""
        if not cr_ids:
            return
        try:
            with self._get_connection() as conn:
                params = [(sprint_id, cr_id) for cr_id in cr_ids]
                conn.executemany("INSERT INTO SprintItems (sprint_id, cr_id) VALUES (?, ?)", params)
        except sqlite3.Error as e:
            logging.error(f"Failed to link items to sprint {sprint_id}: {e}")
            raise

    def update_sprint_status(self, sprint_id: str, status: str):
        """Updates the status and end timestamp of a sprint record."""
        end_timestamp = datetime.now(timezone.utc).isoformat()
        query = "UPDATE Sprints SET status = ?, end_timestamp = ? WHERE sprint_id = ?"
        self._execute_query(query, (status, end_timestamp, sprint_id))

    def update_sprint_status_only(self, sprint_id: str, status: str):
        """Updates just the status of a sprint record."""
        # Note: We are not updating the end_timestamp here, as this is for non-terminal states.
        query = "UPDATE Sprints SET status = ? WHERE sprint_id = ?"
        self._execute_query(query, (status, sprint_id))

    def get_items_for_sprint(self, sprint_id: str) -> list:
        """Retrieves all CR items associated with a given sprint."""
        query = """
        SELECT cr.* FROM ChangeRequestRegister cr
        JOIN SprintItems si ON cr.cr_id = si.cr_id
        WHERE si.sprint_id = ?
        """
        return self._execute_query(query, (sprint_id,), fetch="all")

    def get_sprints_by_status(self, project_id: str, statuses: list[str]) -> list:
        """
        Retrieves Sprints for a project that match one of the given statuses,
        ordered by start time descending (newest first).
        """
        if not statuses:
            return []

        placeholders = ', '.join('?' for _ in statuses)
        query = f"""
            SELECT sprint_id, sprint_goal, start_timestamp, status
            FROM Sprints
            WHERE project_id = ? AND status IN ({placeholders})
            ORDER BY start_timestamp DESC
        """
        params = [project_id]
        params.extend(statuses)

        try:
            return self._execute_query(query, tuple(params), fetch="all")
        except sqlite3.Error as e:
            logging.error(f"Failed to get sprints by status: {e}")
            return []

    def get_latest_sprint_for_project(self, project_id: str):
        """Retrieves the most recent sprint record for a project."""
        query = "SELECT * FROM Sprints WHERE project_id = ? ORDER BY start_timestamp DESC LIMIT 1"
        return self._execute_query(query, (project_id,), fetch="one")

    def get_all_sprints_for_project(self, project_id: str) -> list:
        """Retrieves all sprint records for a project, sorted from newest to oldest."""
        query = "SELECT * FROM Sprints WHERE project_id = ? ORDER BY start_timestamp DESC"
        return self._execute_query(query, (project_id,), fetch="all")

    def delete_sprint_links(self, sprint_id: str):
        """Deletes all item links for a given sprint from SprintItems."""
        query = "DELETE FROM SprintItems WHERE sprint_id = ?"
        self._execute_query(query, (sprint_id,))
        logging.info(f"Removed all item links for sprint {sprint_id}.")

    def delete_sprint(self, sprint_id: str):
        """Deletes a sprint record from the Sprints table."""
        query = "DELETE FROM Sprints WHERE sprint_id = ?"
        self._execute_query(query, (sprint_id,))
        logging.info(f"Deleted sprint record for sprint {sprint_id}.")

    def get_all_plan_jsons_for_project(self, project_id: str) -> dict:
        """
        Retrieves the main development plan and all sprint plans for a project.

        Args:
            project_id (str): The ID of the project.

        Returns:
            A dictionary containing 'dev_plan' (str or None) and
            'sprint_plans' (list of str). Returns empty dict if project not found.
        """
        logging.debug(f"Fetching all plan JSONs for project_id: {project_id}")
        plans = {'dev_plan': None, 'sprint_plans': []}
        try:
            # Fetch the main development plan
            project_row = self._execute_query(
                "SELECT development_plan_text FROM Projects WHERE project_id = ?",
                (project_id,),
                fetch="one"
            )
            if project_row:
                plans['dev_plan'] = project_row['development_plan_text']

            # Fetch all sprint plans
            sprint_rows = self._execute_query(
                "SELECT sprint_plan_json FROM Sprints WHERE project_id = ? ORDER BY start_timestamp ASC",
                (project_id,),
                fetch="all"
            )
            if sprint_rows:
                plans['sprint_plans'] = [row['sprint_plan_json'] for row in sprint_rows if row['sprint_plan_json']]

            logging.debug(f"Found dev_plan: {'Yes' if plans['dev_plan'] else 'No'}, Found {len(plans['sprint_plans'])} sprint plans.")
            return plans
        except Exception as e:
            logging.error(f"Failed to retrieve plan JSONs for project {project_id}: {e}", exc_info=True)
            # Return empty structure on error to avoid crashing the caller
            return {'dev_plan': None, 'sprint_plans': []}

    def batch_update_cr_order(self, order_mapping: list[tuple[int, int]]):
        """
        Updates the display_order for multiple CRs in a single transaction.

        Args:order_mapping (list[tuple[int, int]]): A list of tuples, where each
                                                tuple is (new_display_order, cr_id).
        """
        if not order_mapping:
            return
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    "UPDATE ChangeRequestRegister SET display_order = ? WHERE cr_id = ?",
                    order_mapping
                )
                conn.commit()
                logging.info(f"Successfully batch-updated display order for {len(order_mapping)} items.")
        except sqlite3.Error as e:
            logging.error(f"Failed to batch-update CR display order: {e}")
            raise

    def batch_update_cr_status(self, cr_ids: list[int], new_status: str):
        """
        Updates the status for multiple CRs in a single transaction.

        Args:
            cr_ids (list[int]): A list of cr_id values to update.
            new_status (str): The new status to set for all specified items.
        """
        if not cr_ids:
            return
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            placeholders = ', '.join('?' for _ in cr_ids)
            query = f"UPDATE ChangeRequestRegister SET status = ?, last_modified_timestamp = ? WHERE cr_id IN ({placeholders})"
            params = (new_status, timestamp) + tuple(cr_ids)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                logging.info(f"Successfully batch-updated status to '{new_status}' for {len(cr_ids)} items.")
        except sqlite3.Error as e:
            logging.error(f"Failed to batch-update CR status: {e}")
            raise

    def update_cr_external_link(self, cr_id: int, external_id: str, external_url: str):
        """Updates a CR with its external ID and URL after a successful sync."""
        timestamp = datetime.now(timezone.utc).isoformat()
        query = "UPDATE ChangeRequestRegister SET external_id = ?, external_url = ?, last_modified_timestamp = ? WHERE cr_id = ?"
        self._execute_query(query, (external_id, external_url, timestamp, cr_id))

    def save_orchestration_state(self, project_id: str, current_phase: str, current_step: str, state_details: str, timestamp: str):
        self._execute_query("INSERT OR REPLACE INTO OrchestrationState (project_id, current_phase, current_step, state_details, last_updated) VALUES (?, ?, ?, ?, ?)", (project_id, current_phase, current_step, state_details, timestamp))

    def get_any_paused_state(self) -> Optional[sqlite3.Row]:
        return self._execute_query("SELECT * FROM OrchestrationState LIMIT 1", fetch="one")

    def get_orchestration_state_for_project(self, project_id: str) -> Optional[sqlite3.Row]:
        """Retrieves the saved orchestration state for a specific project."""
        return self._execute_query("SELECT * FROM OrchestrationState WHERE project_id = ?", (project_id,), fetch="one")

    def delete_orchestration_state_for_project(self, project_id: str):
        self._execute_query("DELETE FROM OrchestrationState WHERE project_id = ?", (project_id,))

    def update_cr_impact_analysis(self, cr_id: int, rating: str, details: str, artifact_ids: list[str]):
        ids_json = json.dumps(artifact_ids)
        timestamp = datetime.now(timezone.utc).isoformat()
        query = "UPDATE ChangeRequestRegister SET impact_rating = ?, impact_analysis_details = ?, impacted_artifact_ids = ?, status = 'IMPACT_ANALYZED', last_modified_timestamp = ? WHERE cr_id = ?"
        self._execute_query(query, (rating, details, ids_json, timestamp, cr_id))

    def update_cr_full_analysis(self, cr_id: int, rating: str, details: str, artifact_ids: list[str], preview_text: str):
        logging.debug(f"DB MANAGER: Received preview_text='{preview_text[:200]}...' for cr_id={cr_id}")
        """
        Updates a CR with the full, consolidated analysis results in a single transaction.
        Sets the status to IMPACT_ANALYZED.
        """
        ids_json = json.dumps(artifact_ids)
        timestamp = datetime.now(timezone.utc).isoformat()
        query = """
            UPDATE ChangeRequestRegister SET
                impact_rating = ?,
                impact_analysis_details = ?,
                impacted_artifact_ids = ?,
                technical_preview_text = ?,
                status = 'IMPACT_ANALYZED',
                last_modified_timestamp = ?
            WHERE cr_id = ?
        """
        params = (rating, details, ids_json, preview_text, timestamp, cr_id)
        self._execute_query(query, params)

    def update_cr_technical_preview(self, cr_id: int, preview_text: str):
        """Updates a CR with the generated technical preview text and sets its
        status to TECHNICAL_PREVIEW_COMPLETE.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        query = "UPDATE ChangeRequestRegister SET technical_preview_text = ?, status = 'TECHNICAL_PREVIEW_COMPLETE', last_modified_timestamp = ? WHERE cr_id = ?"
        self._execute_query(query, (preview_text, timestamp, cr_id))

    def update_cr_status(self, cr_id: int, new_status: str):
        timestamp = datetime.now(timezone.utc).isoformat()
        query = "UPDATE ChangeRequestRegister SET status = ?, last_modified_timestamp = ? WHERE cr_id = ?"
        self._execute_query(query, (new_status, timestamp, cr_id))

    def update_cr_field(self, cr_id: int, field_name: str, value: any):
        """Surgically updates a single field for a given CR item."""
        timestamp = datetime.now(timezone.utc).isoformat()
        query = f"UPDATE ChangeRequestRegister SET {field_name} = ?, last_modified_timestamp = ? WHERE cr_id = ?"
        self._execute_query(query, (value, timestamp, cr_id))

    def update_change_request(self, cr_id: int, new_data: dict):
        """
        Updates a CR record with new data. If the status was IMPACT_ANALYZED,
        it reverts to its base state; otherwise, the status is preserved.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        new_description = new_data.get('description')
        new_complexity = new_data.get('complexity')

        cr_details = self.get_cr_by_id(cr_id)
        if not cr_details:
            raise ValueError(f"Could not find CR with ID {cr_id} to update.")

        # Determine the new status based on the required logic
        current_status = cr_details['status']
        request_type = cr_details['request_type']
        new_status = current_status # Default to keeping the status the same

        if current_status == 'IMPACT_ANALYZED':
            if request_type == 'BUG_REPORT':
                new_status = 'BUG_RAISED'
            else: # For BACKLOG_ITEM, CHANGE_REQUEST
                new_status = 'CHANGE_REQUEST'

        # Prepare query parts
        base_query = "UPDATE ChangeRequestRegister SET description = ?, complexity = ?, status = ?, last_modified_timestamp = ?, impact_analysis_details = NULL"
        params = [new_description, new_complexity, new_status, timestamp]

        if request_type == 'BUG_REPORT':
            new_severity = new_data.get('severity')
            query_extension = ", impact_rating = ?"
            params.append(new_severity)
        else:
            new_priority = new_data.get('priority')
            query_extension = ", priority = ?, impact_rating = NULL"
            params.append(new_priority)

        final_query = f"{base_query}{query_extension} WHERE cr_id = ?"
        params.append(cr_id)

        self._execute_query(final_query, tuple(params))

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

    def get_change_requests_filtered(self, project_id: str, statuses: list[str] | None = None, types: list[str] | None = None) -> list:
        """
        Retrieves ChangeRequestRegister records for a project, optionally filtered
        by lists of statuses and/or request types.
        Returns items ordered by display_order.
        """
        if not statuses and not types:
            # If no filters, use the existing efficient method
            return self.get_all_change_requests_for_project(project_id)

        query_parts = ["SELECT * FROM ChangeRequestRegister WHERE project_id = ?"]
        params = [project_id]

        if statuses:
            placeholders = ', '.join('?' for _ in statuses)
            query_parts.append(f"AND status IN ({placeholders})")
            params.extend(statuses)

        if types:
            placeholders = ', '.join('?' for _ in types)
            query_parts.append(f"AND request_type IN ({placeholders})")
            params.extend(types)

        query_parts.append("ORDER BY display_order ASC")
        final_query = " ".join(query_parts)

        logging.debug(f"Executing filtered CR query: {final_query} with params: {params}")
        try:
            return self._execute_query(final_query, tuple(params), fetch="all")
        except sqlite3.Error as e:
            logging.error(f"Failed to execute filtered CR query: {e}")
            return []

    def update_artifact_status(self, artifact_id: str, status: str, timestamp: str):
        query = "UPDATE Artifacts SET status = ?, last_modified_timestamp = ? WHERE artifact_id = ?"
        self._execute_query(query, (status, timestamp, artifact_id))

    def add_document_log_entry(self, project_id: str, document_path: str, author: str, log_text: str, status: str = ""):
        """
        Adds a new entry to the document review log.

        Args:
            project_id: The ID of the project.
            document_path: The relative path of the document the log is for.
            author: The author of the log entry (e.g., 'DEVELOPER', 'CLIENT', 'SYSTEM').
            log_text: The content of the log entry.
            status: An optional status, like 'APPROVED'.
        """
        log_id = f"log_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc).isoformat()
        query = """
            INSERT INTO DocumentReviewLog (
                log_id, project_id, document_path, timestamp, author, log_text, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        values = (log_id, project_id, document_path, timestamp, author, log_text, status)
        try:
            self._execute_query(query, values)
            logging.info(f"Added new document log entry for '{document_path}'")
        except Exception as e:
            logging.error(f"Failed to add document log entry: {e}", exc_info=True)
            raise

    def get_document_log(self, project_id: str, document_path: str) -> list[dict]:
        """
        Retrieves all log entries for a specific document, ordered chronologically.

        Args:
            project_id: The ID of the project.
            document_path: The relative path of the document to get the log for.

        Returns:
            A list of dictionaries, where each dict is a log entry.
        """
        query = """
            SELECT timestamp, author, log_text, status
            FROM DocumentReviewLog
            WHERE project_id = ? AND document_path = ?
            ORDER BY timestamp DESC
        """
        try:
            rows = self._execute_query(query, (project_id, document_path), fetch="all")
            return [dict(row) for row in rows]
        except Exception as e:
            logging.error(f"Database error while fetching document log: {e}", exc_info=True)
            return []