import os
import sys
import zipfile
import shutil
import urllib.request
from pathlib import Path

def fetch_graphviz(project_root):
    print("--- Fetching Graphviz Sidecar (Version 14.0.2) ---")

    # CORRECTED URL provided by user
    GV_URL = "https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/14.0.2/windows_10_cmake_Release_Graphviz-14.0.2-win64.zip"

    dep_dir = project_root / "dependencies"
    gv_dir = dep_dir / "graphviz"
    zip_path = dep_dir / "graphviz.zip"

    # 1. Clean Start
    if gv_dir.exists():
        print("Removing existing graphviz directory...")
        shutil.rmtree(gv_dir)

    dep_dir.mkdir(exist_ok=True)

    # 2. Download
    print(f"Downloading Graphviz from GitLab...")
    try:
        # Add a user-agent to avoid some 403/404 issues with generic scrapers
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(GV_URL, zip_path)
    except Exception as e:
        print(f"Failed to download Graphviz: {e}")
        return False

    # 3. Extract
    print("Extracting...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(dep_dir)
    except Exception as e:
        print(f"Failed to extract zip: {e}")
        return False

    # 4. Organize (Flatten the folder structure)
    # The zip usually extracts to 'Graphviz-14.0.2-win64'
    # We want it at 'dependencies/graphviz'
    extracted_folders = [f for f in dep_dir.iterdir() if f.is_dir() and "graphviz" in f.name.lower()]

    if extracted_folders:
        # If multiple found (unlikely), pick the one that isn't the final dest
        source = extracted_folders[0]
        if source != gv_dir:
            source.rename(gv_dir)
        print(f"Graphviz installed to: {gv_dir}")
    else:
        print("Error: Could not locate extracted folder. Check dependencies/ folder content.")
        return False

    # 5. Cleanup
    if zip_path.exists():
        zip_path.unlink()

    # 6. Verification
    dot_exe = gv_dir / "bin" / "dot.exe"
    if dot_exe.exists():
        print("✅ SUCCESS: Graphviz binary verified.")
        return True
    else:
        print(f"❌ ERROR: dot.exe not found at {dot_exe}")
        return False

if __name__ == "__main__":
    root = Path(__file__).parent.parent
    fetch_graphviz(root)