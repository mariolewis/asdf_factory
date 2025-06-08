import logging
import uuid
from datetime import datetime
from enum import Enum, auto

from asdf_db_manager import ASDFDBManager

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FactoryPhase(Enum):
    """Enumeration for the main factory F-Phases."""
    IDLE = auto()
    ENV_SETUP_TARGET_APP = auto()
    SPEC_ELABORATION = auto()
    PLANNING = auto()
    # Add other phases as they are developed

class MasterOrchestrator:
    """
    The central state machine and workflow manager for the ASDF.
    It coordinates agents, manages project state, and handles project lifecycle.
    """

    def __init__(self, db_path: str):
        """
        Initializes the MasterOrchestrator.

        Args:
            db_path (str): The path to the ASDF's SQLite database.
        """
        self.db_manager = ASDFDBManager(db_path)
        self.project_id: str | None = None
        self.project_name: str | None = None
        self.current_phase: FactoryPhase = FactoryPhase.IDLE

        # Ensure core tables exist on startup
        with self.db_manager as db:
            db.create_tables()

        logging.info("MasterOrchestrator initialized.")

    def get_status(self) -> dict:
        """Returns the current status of the orchestrator."""
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "current_phase": self.current_phase.name
        }

    def start_new_project(self, project_name: str):
        """
        Initializes a new project.

        This method follows the logic for 'Start New Project' from F-Phase 7.
        It creates a new project record in the database and sets the orchestrator's
        state to begin the development process for the new project.

        Args:
            project_name (str): The human-readable name for the new project.
        """
        if self.project_id:
            logging.warning(f"A project '{self.project_name}' is already active. Starting a new one will override it in this session.")
            # [cite_start]In a future implementation, we would call the Stop & Export logic here as per PRD[cite: 312].

        self.project_id = f"proj_{uuid.uuid4().hex[:8]}"
        self.project_name = project_name
        self.current_phase = FactoryPhase.ENV_SETUP_TARGET_APP # Set initial phase after start
        timestamp = datetime.utcnow().isoformat()

        try:
            with self.db_manager as db:
                db.create_project(self.project_id, self.project_name, timestamp)
            logging.info(f"Successfully started new project: '{self.project_name}' (ID: {self.project_id})")
            logging.info(f"Orchestrator status: {self.get_status()}")
        except Exception as e:
            logging.error(f"Failed to start new project '{self.project_name}': {e}")
            # Reset state on failure
            self.project_id = None
            self.project_name = None
            self.current_phase = FactoryPhase.IDLE
            raise

    def set_phase(self, phase_name: str):
        """
        Sets the current project phase.

        This provides a controlled way for the GUI or other components to
        signal a transition in the factory's workflow.

        Args:
            phase_name (str): The name of the phase to transition to
                              (e.g., "SPEC_ELABORATION").
        """
        if not self.project_id:
            logging.error("Cannot set phase; no active project.")
            return

        try:
            # Find the corresponding Enum member from the string name
            new_phase = FactoryPhase[phase_name]
            self.current_phase = new_phase
            logging.info(f"Project '{self.project_name}' phase changed to: {self.current_phase.name}")
            # In a future implementation, this would also save the state
            # to the OrchestrationState table in the database.
        except KeyError:
            logging.error(f"Attempted to set an invalid phase: {phase_name}")

    def pause_project(self):
        """
        Pauses the currently active project. (Placeholder)

        As per F-Phase 7, this will save the complete current state of the
        orchestration to the database, allowing for a graceful pause.
        [cite_start]The project remains the active project. [cite: 314, 315]
        """
        if not self.project_id:
            logging.warning("No active project to pause.")
            return

        logging.info(f"Placeholder: Pausing project '{self.project_name}'.")
        # Future implementation will save the detailed state to the DB.
        self.current_phase = FactoryPhase.IDLE # Example of a state change
        pass

    def resume_project(self):
        """
        Resumes a paused project. (Placeholder)

        As per F-Phase 7, this will load the last saved state from the
        [cite_start]database and resume operations from the appropriate phase and step. [cite: 316]
        """
        if not self.project_id:
            logging.warning("No active project to resume.")
            return

        logging.info(f"Placeholder: Resuming project '{self.project_name}'.")
        # Future implementation will load state from DB and set the correct phase.
        pass

    def discontinue_project(self):
        """
        Discontinues the currently active project. (Placeholder)

        [cite_start]As per F-Phase 3 PM Checkpoints, this option halts the project. [cite: 266]
        This is a placeholder for the 'Stop & Export' or 'Delete' logic.
        """
        if not self.project_id:
            logging.warning("No active project to discontinue.")
            return

        logging.info(f"Placeholder: Discontinuing project '{self.project_name}'.")
        # Future implementation will handle archival and cleanup.
        self.project_id = None
        self.project_name = None
        self.current_phase = FactoryPhase.IDLE
        pass