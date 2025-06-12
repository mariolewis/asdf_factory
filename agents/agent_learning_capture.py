# agents/agent_learning_capture.py

"""
This module contains the LearningCaptureAgent class.
"""

import logging
from datetime import datetime, timezone
from asdf_db_manager import ASDFDBManager

class LearningCaptureAgent:
    """
    Agent responsible for capturing high-value interactions and learnings
    and storing them in the Factory's internal Knowledge Base.
    (ASDF PRD v0.4, F-Phase 8)
    """

    def __init__(self, db_manager: ASDFDBManager):
        """
        Initializes the LearningCaptureAgent.

        Args:
            db_manager (ASDFDBManager): An instance of the database manager (DAO)
                                        to interact with the ASDF database.
        """
        if not db_manager:
            raise ValueError("Database manager cannot be None.")
        self.db_manager = db_manager
        logging.info("LearningCaptureAgent initialized.")

    def add_learning_entry(self, context: str, problem: str, solution: str, tags: list[str]) -> bool:
        """
        Structures and saves a new entry to the FactoryKnowledgeBase.

        This method is called by the MasterOrchestrator when a significant
        learning opportunity is identified (e.g., a successful manual debug,
        a critical specification clarification).

        Args:
            context (str): The situation or project context where the learning occurred.
            problem (str): A description of the problem, ambiguity, or error.
            solution (str): The successful clarification, fix, or solution.
            tags (list[str]): A list of keywords for easy searching and retrieval.

        Returns:
            bool: True if the entry was saved successfully, False otherwise.
        """
        if not all([context, problem, solution, tags]):
            logging.warning("Attempted to add an incomplete learning entry. All fields are required.")
            return False

        try:
            # The DAO expects tags as a comma-separated string
            tags_str = ", ".join(sorted(list(set(tag.strip().lower() for tag in tags))))
            timestamp = datetime.now(timezone.utc).isoformat()

            with self.db_manager as db:
                db.add_kb_entry(
                    context=context,
                    problem=problem,
                    solution=solution,
                    tags=tags_str,
                    timestamp=timestamp
                )
            logging.info(f"Successfully added new learning entry to knowledge base with tags: {tags_str}")
            return True

        except Exception as e:
            logging.error(f"Failed to add learning entry to knowledge base. Error: {e}")
            return False