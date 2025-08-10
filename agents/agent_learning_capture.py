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
    """

    def __init__(self, db_manager: ASDFDBManager):
        """
        Initializes the LearningCaptureAgent.
        """
        if not db_manager:
            raise ValueError("Database manager cannot be None.")
        self.db_manager = db_manager
        logging.info("LearningCaptureAgent initialized.")

    def add_learning_entry(self, context: str, problem: str, solution: str, tags: list[str]) -> bool:
        """
        Structures and saves a new entry to the FactoryKnowledgeBase.
        """
        if not all([context, problem, solution, tags]):
            logging.warning("Attempted to add an incomplete learning entry. All fields are required.")
            return False

        try:
            tags_str = ", ".join(sorted(list(set(tag.strip().lower() for tag in tags))))
            timestamp = datetime.now(timezone.utc).isoformat()

            # Corrected: Direct call to the db_manager
            self.db_manager.add_kb_entry(
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