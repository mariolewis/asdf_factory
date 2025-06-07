import os
import uuid
import logging
from datetime import datetime
from asdf_db_manager import ASDFDBManager, Artifact

# Configure logging for the test script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_tests():
    """
    Runs a series of tests on the ASDFDBManager to verify CRUD operations.
    """
    test_db_path = "test_asdf.db"
    logging.info(f"--- Starting DAO Tests ---")
    logging.info(f"Using temporary database: {test_db_path}")

    # Ensure the test database file doesn't exist before starting
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    try:
        with ASDFDBManager(test_db_path) as db:
            # 1. Test Table Creation
            logging.info("Step 1: Testing table creation...")
            db.create_tables()
            logging.info("-> Table creation executed.")

            # 2. Test Project CRUD
            logging.info("\nStep 2: Testing Project CRUD...")
            project_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            db.create_project(project_id, "Test Project", timestamp)
            retrieved_project = db.get_project_by_id(project_id)
            assert retrieved_project is not None, "Failed to retrieve project."
            assert retrieved_project['project_name'] == "Test Project", "Project name mismatch."
            logging.info("-> Project CRUD tests passed.")

            # 3. Test Artifact CRUD
            logging.info("\nStep 3: Testing Artifact CRUD...")
            artifact_id = str(uuid.uuid4())
            artifact_obj = Artifact(
                artifact_id=artifact_id,
                project_id=project_id,
                status="SPECIFIED",
                last_modified_timestamp=datetime.utcnow().isoformat(),
                artifact_name="test_function",
                artifact_type="FUNCTION"
            )
            db.create_artifact(artifact_obj)
            retrieved_artifact = db.get_artifact_by_id(artifact_id)
            assert retrieved_artifact is not None, "Failed to retrieve artifact."
            assert retrieved_artifact['artifact_name'] == "test_function", "Artifact name mismatch."

            db.update_artifact_status(artifact_id, "CODING_COMPLETED", datetime.utcnow().isoformat())
            updated_artifact = db.get_artifact_by_id(artifact_id)
            assert updated_artifact['status'] == "CODING_COMPLETED", "Artifact status update failed."
            logging.info("-> Artifact CRUD tests passed.")

            # 4. Test Reporting Queries
            logging.info("\nStep 4: Testing Reporting Queries...")
            counts = db.get_component_counts_by_status(project_id)
            assert counts.get("CODING_COMPLETED") == 1, "Status count is incorrect."
            pending_artifacts = db.get_artifacts_by_statuses(project_id, ["CODING_COMPLETED", "SPECIFIED"])
            assert len(pending_artifacts) == 1, "Artifact retrieval by statuses failed."
            logging.info("-> Reporting query tests passed.")

            # 5. Test Config CRUD
            logging.info("\nStep 5: Testing Config CRUD...")
            db.set_config_value("GEMINI_API_KEY", "test_key_12345")
            api_key = db.get_config_value("GEMINI_API_KEY")
            assert api_key == "test_key_12345", "Failed to get config value."
            all_config = db.get_all_config_values()
            assert "GEMINI_API_KEY" in all_config, "Failed to get all config values."
            logging.info("-> Config CRUD tests passed.")

            # 6. Test History CRUD
            logging.info("\nStep 6: Testing History CRUD...")
            db.add_project_to_history(project_id, "Test Project", "/path/to/project", "/path/to/archive.zip", timestamp)
            history_list = db.get_project_history()
            assert len(history_list) == 1, "Failed to add project to history."
            assert history_list[0]['project_name'] == "Test Project", "History project name mismatch."
            logging.info("-> History CRUD tests passed.")

        logging.info("\n--- All DAO tests passed successfully! ---")

    except AssertionError as e:
        logging.error(f"!!! TEST FAILED: {e} !!!")
    except Exception as e:
        logging.error(f"An unexpected error occurred during testing: {e}", exc_info=True)
    finally:
        # Clean up the test database file
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            logging.info(f"\nTemporary database '{test_db_path}' removed.")


if __name__ == "__main__":
    run_tests()