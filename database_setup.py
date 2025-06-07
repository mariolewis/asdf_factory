import sqlite3
from sqlite3 import Error
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def create_connection(db_file):
    """ Create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        logging.info(f"Successfully connected to SQLite database: {db_file}")
    except Error as e:
        logging.error(f"Error connecting to database: {e}")
    return conn

def create_tables(conn):
    """ Create tables in the SQLite database """
    if conn is not None:
        # We will add SQL statements here in the next steps
        logging.info("Table creation step initiated.")
        try:
            cursor = conn.cursor()
            # SQL statement to create the Projects table
            # [cite_start]This table will initially serve as a simple record. [cite: 22]
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Projects (
                    project_id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    creation_timestamp TEXT NOT NULL,
                    status TEXT NOT NULL
                );
            """)
            logging.info("Table 'Projects' created successfully or already exists.")
            # SQL statement to create the Artifacts table (Record-of-Work-Done)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Artifacts (
                    artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    file_path TEXT,
                    artifact_name TEXT,
                    artifact_type TEXT,
                    signature TEXT,
                    short_description TEXT,
                    version INTEGER,
                    status TEXT,
                    last_modified_timestamp TEXT NOT NULL,
                    commit_hash TEXT,
                    micro_spec_id TEXT,
                    dependencies TEXT,
                    unit_test_status TEXT,
                    FOREIGN KEY (project_id) REFERENCES Projects (project_id)
                );
            """)
            logging.info("Table 'Artifacts' created successfully or already exists.")
            # SQL statement to create the OrchestrationState table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS OrchestrationState (
                    project_id TEXT PRIMARY KEY,
                    current_f_phase TEXT,
                    status_details TEXT,
                    last_saved_timestamp TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES Projects (project_id)
                );
            """)
            logging.info("Table 'OrchestrationState' created successfully or already exists.")
            # SQL statement to create the FactoryConfig table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS FactoryConfig (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)
            logging.info("Table 'FactoryConfig' created successfully or already exists.")
            # SQL statement to create the FactoryKnowledgeBase table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS FactoryKnowledgeBase (
                    learning_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    problem_context TEXT NOT NULL,
                    solution_or_clarification TEXT NOT NULL,
                    category TEXT,
                    creation_timestamp TEXT NOT NULL
                );
            """)
            logging.info("Table 'FactoryKnowledgeBase' created successfully or already exists.")
            # SQL statement to create the ProjectHistory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ProjectHistory (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    project_name TEXT,
                    project_root_folder TEXT,
                    archive_file_path TEXT,
                    last_stop_timestamp TEXT NOT NULL
                );
            """)
            logging.info("Table 'ProjectHistory' created successfully or already exists.")
        except Error as e:
            logging.error(f"Error creating tables: {e}")
    else:
        logging.error("Database connection is not established.")

def main():
    """ Main function to set up the database """
    database_file = "asdf_main.db"

    # Create a database connection
    conn = create_connection(database_file)

    # Create tables
    create_tables(conn)

    # Close the connection
    if conn:
        conn.close()
        logging.info("Database connection closed.")

if __name__ == '__main__':
    main()