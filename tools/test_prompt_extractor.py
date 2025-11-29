import unittest
import shutil
import os
from pathlib import Path
import textwrap
from extract_prompts import extract_prompts_from_file

class TestPromptExtractor(unittest.TestCase):

    def setUp(self):
        # Setup temporary directories
        self.test_dir = Path("temp_test_env")
        self.output_dir = self.test_dir / "data" / "prompts"
        self.source_file = self.test_dir / "dummy_agent.py"

        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create a dummy python file with various prompt styles
        dummy_code = textwrap.dedent("""
            import textwrap

            class DummyAgent:
                def __init__(self):
                    self.context = "Project Context"

                def run(self):
                    # Case 1: Standard f-string
                    simple_prompt = f"Hello {self.context}"

                    # Case 2: textwrap.dedent with triple quotes
                    dedent_prompt = textwrap.dedent(f\"\"\"
                        You are an expert.
                        Context: {self.context}
                    \"\"\")

                    # Case 3: Standard string (no f-string)
                    static_prompt = "This is a static prompt."

                    # Case 4: Variable with 'template' in name
                    email_template = f"Subject: Update for {self.context}"

                    # Case 5: Ignore this (no 'prompt' or 'template' in name)
                    ignored_variable = "Should not be extracted"
        """)

        with open(self.source_file, 'w', encoding='utf-8') as f:
            f.write(dummy_code)

    def tearDown(self):
        # Clean up temporary files
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_extraction(self):
        # Run the extractor
        extract_prompts_from_file(self.source_file, self.output_dir)

        # Verify Case 1: Simple f-string
        file_1 = self.output_dir / "dummy_agent__simple_prompt.txt"
        self.assertTrue(file_1.exists(), "Failed to extract simple_prompt")
        content_1 = file_1.read_text(encoding='utf-8')
        self.assertEqual(content_1, "Hello {self.context}")

        # Verify Case 2: Dedent + Multiline
        file_2 = self.output_dir / "dummy_agent__dedent_prompt.txt"
        self.assertTrue(file_2.exists(), "Failed to extract dedent_prompt")
        content_2 = file_2.read_text(encoding='utf-8')
        expected_2 = "\nYou are an expert.\nContext: {self.context}\n"
        self.assertEqual(content_2.strip(), expected_2.strip())

        # Verify Case 3: Static string
        file_3 = self.output_dir / "dummy_agent__static_prompt.txt"
        self.assertTrue(file_3.exists())
        self.assertEqual(file_3.read_text(encoding='utf-8'), "This is a static prompt.")

        # Verify Case 4: Template naming convention
        file_4 = self.output_dir / "dummy_agent__email_template.txt"
        self.assertTrue(file_4.exists())
        self.assertEqual(file_4.read_text(encoding='utf-8'), "Subject: Update for {self.context}")

        # Verify Case 5: Ignored variable
        file_5 = self.output_dir / "dummy_agent__ignored_variable.txt"
        self.assertFalse(file_5.exists(), "Wrongly extracted a variable without 'prompt/template' in name")

if __name__ == '__main__':
    unittest.main()