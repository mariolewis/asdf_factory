# agents/agent_traceability_report.py

import logging
import json
from klyve_db_manager import KlyveDBManager
# Import MasterOrchestrator to access the hierarchical numbering method
# from master_orchestrator import MasterOrchestrator

class RequirementTraceabilityAgent:
    """
    Agent responsible for gathering data to trace requirements from the backlog
    down to implemented code artifacts.
    """

    def __init__(self, db_manager: KlyveDBManager, orchestrator: 'MasterOrchestrator'):
        """
        Initializes the RequirementTraceabilityAgent.

        Args:
            db_manager (KlyveDBManager): An instance of the database manager.
            orchestrator (MasterOrchestrator): An instance of the main orchestrator
                                               (needed for hierarchical IDs).
        """
        if not db_manager:
            raise ValueError("db_manager is required for RequirementTraceabilityAgent.")
        if not orchestrator:
            raise ValueError("orchestrator is required for RequirementTraceabilityAgent.")

        self.db_manager = db_manager
        self.orchestrator = orchestrator # Store orchestrator instance
        logging.info("RequirementTraceabilityAgent initialized.")

    def _parse_plan_json(self, plan_json_str: str | None) -> list:
        """Safely parses a plan JSON string into a list of tasks."""
        if not plan_json_str:
            return []
        try:
            plan_data = json.loads(plan_json_str)
            # Handle both old plan format (dict) and new plan format (list)
            if isinstance(plan_data, dict):
                return plan_data.get("development_plan", [])
            elif isinstance(plan_data, list):
                # Check if it's a list containing an error object
                if plan_data and isinstance(plan_data[0], dict) and "error" in plan_data[0]:
                    logging.warning(f"Parsed plan JSON contains an error: {plan_data[0]['error']}")
                    return []
                return plan_data # Assume it's a list of task dicts
            else:
                logging.warning(f"Plan JSON is not a dict or list: {type(plan_data)}")
                return []
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse plan JSON: {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error parsing plan JSON: {e}", exc_info=True)
            return []

    def generate_trace_data(self, project_id: str) -> list:
        """
        Generates the traceability data by linking backlog items to artifacts.

        Args:
            project_id (str): The ID of the project.

        Returns:
            A list of dictionaries, where each dictionary represents a link
            between a backlog item and an implemented artifact (or indicates
            no artifact found). Uses hierarchical_id for backlog items.
        """
        logging.info(f"Generating traceability data for project {project_id}")
        trace_results = []

        try:
            # 1. Get full backlog with hierarchical IDs from the orchestrator
            # We need the orchestrator instance to call this method
            full_backlog_hierarchy = self.orchestrator._get_backlog_with_hierarchical_numbers()
            if not full_backlog_hierarchy:
                logging.warning("No backlog items found for traceability report.")
                return []

            # Flatten the hierarchy for easier lookup
            flat_backlog = {item['cr_id']: item for item in self.orchestrator._flatten_hierarchy(full_backlog_hierarchy)}

            # 2. Get all relevant plan JSONs
            plan_jsons = self.db_manager.get_all_plan_jsons_for_project(project_id)
            all_tasks = []
            if plan_jsons.get('dev_plan'):
                all_tasks.extend(self._parse_plan_json(plan_jsons['dev_plan']))
            for sprint_plan in plan_jsons.get('sprint_plans', []):
                all_tasks.extend(self._parse_plan_json(sprint_plan))

            logging.debug(f"Parsed a total of {len(all_tasks)} tasks from all plans.")

            # 3. Create a map from cr_id to relevant task micro_spec_ids
            cr_to_micro_spec_ids = {}
            for task in all_tasks:
                micro_spec_id = task.get("micro_spec_id")
                parent_cr_ids = task.get("parent_cr_ids", [])
                if micro_spec_id and parent_cr_ids:
                    for cr_id in parent_cr_ids:
                        if cr_id not in cr_to_micro_spec_ids:
                            cr_to_micro_spec_ids[cr_id] = set()
                        cr_to_micro_spec_ids[cr_id].add(micro_spec_id)

            logging.debug(f"Mapped {len(cr_to_micro_spec_ids)} cr_ids to micro_spec_ids.")

            # 4. Get all potentially relevant micro_spec_ids and query artifacts
            all_relevant_micro_spec_ids = list(set.union(*cr_to_micro_spec_ids.values())) if cr_to_micro_spec_ids else []
            artifacts = []
            if all_relevant_micro_spec_ids:
                artifacts = self.db_manager.get_artifacts_by_micro_spec_ids(project_id, all_relevant_micro_spec_ids)

            # 5. Create a map from micro_spec_id to artifact(s)
            micro_spec_id_to_artifacts = {}
            for art in artifacts:
                ms_id = art['micro_spec_id']
                if ms_id:
                    if ms_id not in micro_spec_id_to_artifacts:
                        micro_spec_id_to_artifacts[ms_id] = []
                    micro_spec_id_to_artifacts[ms_id].append(dict(art)) # Store as dict

            logging.debug(f"Mapped {len(micro_spec_id_to_artifacts)} micro_spec_ids to {len(artifacts)} artifacts.")

            # 6. Build the final trace results, iterating through the original flat backlog
            for cr_id, backlog_item in flat_backlog.items():
                found_artifact = False
                micro_spec_ids_for_item = cr_to_micro_spec_ids.get(cr_id, set())

                if micro_spec_ids_for_item:
                    for ms_id in micro_spec_ids_for_item:
                        linked_artifacts = micro_spec_id_to_artifacts.get(ms_id, [])
                        if linked_artifacts:
                            for artifact in linked_artifacts:
                                trace_results.append({
                                    'backlog_id': backlog_item.get('hierarchical_id', f'CR-{cr_id}'),
                                    'backlog_title': backlog_item.get('title', 'N/A'),
                                    'backlog_status': backlog_item.get('status', 'N/A'),
                                    'artifact_path': artifact.get('file_path', 'N/A'),
                                    'artifact_name': artifact.get('artifact_name', 'N/A')
                                })
                                found_artifact = True
                        else:
                             # Task existed, but no artifact found (maybe skipped or failed?)
                             pass # We'll add the backlog item row below if no artifacts were ever found

                # If no artifacts were linked *at all* for this backlog item, add a row indicating that
                if not found_artifact:
                    trace_results.append({
                        'backlog_id': backlog_item.get('hierarchical_id', f'CR-{cr_id}'),
                        'backlog_title': backlog_item.get('title', 'N/A'),
                        'backlog_status': backlog_item.get('status', 'N/A'),
                        'artifact_path': 'N/A', # Indicate not implemented
                        'artifact_name': 'N/A'
                    })

            logging.info(f"Generated {len(trace_results)} traceability report entries.")
            # Sort results by hierarchical backlog ID for consistent display
            trace_results.sort(key=lambda x: tuple(map(int, x['backlog_id'].split('.'))) if '.' in x['backlog_id'] else (int(x['backlog_id']),))
            return trace_results

        except Exception as e:
            logging.error(f"Failed during traceability data generation for project {project_id}: {e}", exc_info=True)
            return [] # Return empty list on failure