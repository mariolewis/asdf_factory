# package_context.py

import sys
from pathlib import Path
import docx  # from python-docx
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QClipboard

# --- Configuration ---
# Add or remove file extensions you want to include in the context.
INCLUDED_EXTENSIONS = {
    '.py',
    '.ui',
    '.qss',
    '.txt'
}

# Add directory or file names to ignore.
IGNORED_PATHS = {
    '__pycache__',
    '.git',
    '.venv',
    'venv',
    'env',
    'dist',
    'build',
    'bat',
    'package_context.py' # Ignore the script itself
}
# -------------------

def get_file_content(file_path: Path) -> str:
    """Reads the content of a file, handling .docx and various text encodings."""
    try:
        if file_path.suffix == '.docx':
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        else:
            # For text-based files, read as bytes first to handle encoding issues
            file_bytes = file_path.read_bytes()
            try:
                # Try UTF-8 first (for all .py, .qss, etc.)
                return file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    # Fallback for Windows-created files (like pip freeze >)
                    return file_bytes.decode('utf-16')
                except UnicodeDecodeError:
                    # Final fallback for any other case
                    return file_bytes.decode('latin-1', errors='ignore')
    except Exception as e:
        return f"Error reading file {file_path.name}: {e}"

def package_project_context():
    """
    Traverses the project directory, packages all relevant file contents
    into a single string, and copies it to the clipboard.
    """
    project_root = Path(__file__).parent.resolve()
    print(f"🔍 Starting context packaging from root: {project_root}")

    # This is necessary to use Qt's clipboard functionality in a script
    app = QApplication.instance() or QApplication(sys.argv)
    clipboard = app.clipboard()

    context_blocks = []

    # Use rglob to recursively find all files
    for path in project_root.rglob('*'):
        if path.is_file():
            # Check if any part of the path is in the ignored set
            if any(part in IGNORED_PATHS for part in path.parts):
                continue

            # Check if the file extension is in our include list
            if path.suffix in INCLUDED_EXTENSIONS:
                relative_path = path.relative_to(project_root).as_posix()
                print(f"  -> Packaging: {relative_path}")

                content = get_file_content(path)

                # Format the content with clear delimiters
                block = (
                    f"--- FILE: {relative_path} ---\n"
                    f"{content}\n"
                    f"--- END FILE: {relative_path} ---\n"
                )
                context_blocks.append(block)

    if not context_blocks:
        print("❌ No files found to package. Check your INCLUDED_EXTENSIONS configuration.")
        return

    full_context = "\n".join(context_blocks)
    clipboard.setText(full_context)

    print("\n✅ Project context successfully packaged and copied to clipboard!")
    print(f"   Total characters: {len(full_context):,}")


if __name__ == "__main__":
    package_project_context()
