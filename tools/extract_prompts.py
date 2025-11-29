import ast
import os
import sys
import json
import re
from pathlib import Path
import textwrap

class PromptVisitor(ast.NodeVisitor):
    """
    AST Visitor to find, extract, and index prompts.
    """
    def __init__(self, file_path):
        self.file_path = str(file_path).replace("\\", "/")
        self.prompts = [] # List of dicts

    def _make_safe_placeholder(self, expr):
        """
        Converts any Python expression into a valid alphanumeric identifier.
        Example: "', '.join(list)" -> "join_list"
        """
        clean = re.sub(r'[^a-zA-Z0-9_]', '_', expr)
        clean = re.sub(r'_+', '_', clean)
        clean = clean.strip('_')
        if clean and clean[0].isdigit():
            clean = "v_" + clean
        if not clean:
            clean = "expr"
        return clean

    def _analyze_fstring_variables(self, node):
        """Extracts variable names used inside an f-string for the manifest."""
        variables = []
        if isinstance(node, ast.JoinedStr):
            for value in node.values:
                if isinstance(value, ast.FormattedValue):
                    try:
                        if sys.version_info >= (3, 9):
                            variables.append(ast.unparse(value.value))
                        else:
                            if isinstance(value.value, ast.Name):
                                variables.append(value.value.id)
                            elif isinstance(value.value, ast.Attribute):
                                variables.append("attribute_access")
                    except:
                        pass
        return variables

    def _extract_string_from_node(self, node):
        """Helper to extract text and detect f-string properties."""
        text = None
        is_fstring = False
        variables = []

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value

        elif isinstance(node, ast.JoinedStr):
            is_fstring = True
            variables = self._analyze_fstring_variables(node)
            parts = []
            for value in node.values:
                if isinstance(value, ast.Constant):
                    # FIX: Escape literal braces in f-string constants
                    # This ensures JSON examples like {"key": "val"} become {{ "key": "val" }}
                    # so .format() treats them as literals, not missing variables.
                    val = value.value.replace("{", "{{").replace("}", "}}")
                    parts.append(val)
                elif isinstance(value, ast.FormattedValue):
                    try:
                        if sys.version_info >= (3, 9):
                            raw_expr = ast.unparse(value.value)
                        else:
                            raw_expr = "VAR"

                        safe_placeholder = self._make_safe_placeholder(raw_expr)
                        parts.append(f"{{{safe_placeholder}}}")
                    except:
                        parts.append("{UNKNOWN}")
            text = "".join(parts)

        elif isinstance(node, ast.Call):
            if (isinstance(node.func, ast.Attribute) and node.func.attr == 'dedent') or \
               (isinstance(node.func, ast.Name) and node.func.id == 'dedent'):
                if node.args:
                    inner_text, inner_is_f, inner_vars = self._extract_string_from_node(node.args[0])
                    if inner_text:
                        return textwrap.dedent(inner_text), inner_is_f, inner_vars

        return text, is_fstring, variables

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                if 'prompt' in var_name.lower() or 'template' in var_name.lower():
                    content, is_fstring, variables = self._extract_string_from_node(node.value)
                    if content:
                        if len(content) > 50:
                            self.prompts.append({
                                'file_path': self.file_path,
                                'variable_name': var_name,
                                'content': content,
                                'is_fstring': is_fstring,
                                'variables': variables,
                                'line_start': node.lineno,
                                'line_end': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
                            })
                        else:
                            print(f"[SKIPPED SMALL] {self.file_path} :: {var_name} (Len: {len(content)})")
        self.generic_visit(node)

def extract_prompts_and_build_manifest(project_root, output_dir):
    manifest = {}
    agents_dir = project_root / "agents"

    for f in output_dir.glob("*.txt"):
        f.unlink()

    files_to_scan = [project_root / "master_orchestrator.py"]
    files_to_scan.extend(agents_dir.glob("*.py"))

    total_extracted = 0

    for file_path in files_to_scan:
        if not file_path.exists(): continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)
            visitor = PromptVisitor(file_path.relative_to(project_root))
            visitor.visit(tree)

            for p in visitor.prompts:
                safe_filename = Path(p['file_path']).stem
                vault_key = f"{safe_filename}__{p['variable_name']}_{p['line_start']}"

                txt_filename = f"{vault_key}.txt"
                with open(output_dir / txt_filename, 'w', encoding='utf-8') as f_out:
                    f_out.write(p['content'])

                manifest[vault_key] = {
                    "source_file": str(p['file_path']),
                    "variable_name": p['variable_name'],
                    "vault_key": vault_key,
                    "filename": txt_filename,
                    "is_fstring": p['is_fstring'],
                    "original_variables": p['variables'],
                    "line_start": p['line_start'],
                    "line_end": p['line_end']
                }
                total_extracted += 1
                print(f"Indexed: {vault_key}")

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    manifest_path = project_root / "data" / "prompts_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=4)

    print(f"\nExtraction Complete. {total_extracted} prompts indexed.")

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    out = root / "data" / "prompts"
    out.mkdir(parents=True, exist_ok=True)
    extract_prompts_and_build_manifest(root, out)