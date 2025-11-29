import sys
from pathlib import Path

def patch_orchestrator(project_root):
    target_file = project_root / "master_orchestrator.py"

    if not target_file.exists():
        print(f"Error: Could not find {target_file}")
        return

    print(f"Patching {target_file.name}...")
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # --- FIX 1: Update Method Signature to accept **kwargs (fixes TypeError) ---
    old_sig = "def _run_automated_ui_test_phase(self, progress_callback=None):"
    new_sig = "def _run_automated_ui_test_phase(self, progress_callback=None, **kwargs):"

    if old_sig in content:
        content = content.replace(old_sig, new_sig)
        print("  [FIX 1] Updated _run_automated_ui_test_phase signature.")
    else:
        print("  [WARNING] Could not find _run_automated_ui_test_phase signature. Already patched?")

    # --- FIX 2: Add Logic Check to skip UI Phase for non-GUI apps ---
    # We target the handle_sprint_test_result_ack method
    old_logic = """    def handle_sprint_test_result_ack(self):
        \"\"\"
        Handles the user's acknowledgement of the sprint test results and proceeds.
        \"\"\"
        status = self.task_awaiting_approval.get("sprint_test_status", "FAILURE")
        if status == 'SUCCESS':
            self.set_phase("AWAITING_UI_TEST_DECISION")
        else:"""

    new_logic = """    def handle_sprint_test_result_ack(self):
        \"\"\"
        Handles the user's acknowledgement of the sprint test results and proceeds.
        \"\"\"
        status = self.task_awaiting_approval.get("sprint_test_status", "FAILURE")
        if status == 'SUCCESS':
            # FIX: Check if this is a GUI project before entering UI testing
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if project_details and project_details['is_gui_project'] == 1:
                self.set_phase("AWAITING_UI_TEST_DECISION")
            else:
                logging.info("Non-GUI project detected. Skipping UI Testing phase.")
                self.set_phase("SPRINT_REVIEW")
        else:"""

    # Be careful with whitespace matching. We'll try a slightly looser match if exact fails.
    if old_logic in content:
        content = content.replace(old_logic, new_logic)
        print("  [FIX 2] Updated handle_sprint_test_result_ack logic.")
    else:
        # Fallback: Try to find just the critical if/else block if indentation differs slightly
        print("  [INFO] Exact match for FIX 2 failed. Attempting relaxed match...")
        fallback_search = '        if status == \'SUCCESS\':\n            self.set_phase("AWAITING_UI_TEST_DECISION")'
        fallback_replace = """        if status == 'SUCCESS':
            # FIX: Check if this is a GUI project before entering UI testing
            project_details = self.db_manager.get_project_by_id(self.project_id)
            if project_details and project_details['is_gui_project'] == 1:
                self.set_phase("AWAITING_UI_TEST_DECISION")
            else:
                logging.info("Non-GUI project detected. Skipping UI Testing phase.")
                self.set_phase("SPRINT_REVIEW")"""

        if fallback_search in content:
            content = content.replace(fallback_search, fallback_replace)
            print("  [FIX 2] Updated handle_sprint_test_result_ack logic (Fallback method).")
        else:
            print("  [ERROR] Could not apply FIX 2. Logic block not found.")

    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Orchestrator patch complete.")

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    patch_orchestrator(root)