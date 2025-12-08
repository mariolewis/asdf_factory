import os
import sys
import shutil
import subprocess
import re
from pathlib import Path

# --- Configuration ---
PROJECT_NAME = "Klyve"
BUILD_DIR = Path("build_stage")
DIST_DIR = Path("dist")

# --- LGPL CONFIGURATION (Dynamic Detection) ---
try:
    import PySide6
    # Go up two levels from __init__.py to find the 'site-packages' root
    CLEAN_PYSIDE_ROOT = Path(PySide6.__file__).parent.parent
    print(f"ℹ️  Detected PySide6 source at: {CLEAN_PYSIDE_ROOT}")
except ImportError:
    print("❌ FATAL: PySide6 not found in current environment. Cannot build.")
    sys.exit(1)

def clean_build_env():
    """Removes previous build artifacts."""
    print(f"--- Cleaning {BUILD_DIR} and {DIST_DIR} ---")
    if BUILD_DIR.exists(): shutil.rmtree(BUILD_DIR)
    if DIST_DIR.exists(): shutil.rmtree(DIST_DIR)
    BUILD_DIR.mkdir(exist_ok=True)

def stage_project(project_root):
    """Copies source code to a staging area."""
    print(f"--- Staging Project to {BUILD_DIR} ---")

    def ignore_patterns(path, names):
        return [n for n in names if n in [
            '.git', '__pycache__', 'venv', 'env',
            'dist', 'build', 'backups', 'tests', 'test',
            'squashfs-root',
            BUILD_DIR.name, '.idea', '.vscode', 'data'
        ]]

    dest_src = BUILD_DIR / "src"
    if dest_src.exists(): shutil.rmtree(dest_src)
    shutil.copytree(project_root, dest_src, ignore=ignore_patterns)

    print("--- Staging Data Files ---")
    src_data = project_root / "data"
    dst_data = dest_src / "data"
    dst_data.mkdir(exist_ok=True)

    if (src_data / "prompts").exists():
        shutil.copytree(src_data / "prompts", dst_data / "prompts")
    if (src_data / "prompts_manifest.json").exists():
        shutil.copy2(src_data / "prompts_manifest.json", dst_data / "prompts_manifest.json")
    if (src_data / "templates").exists():
        shutil.copytree(src_data / "templates", dst_data / "templates")

    return dest_src

def sanitize_config(staged_root):
    """Removes plaintext keys from config.py."""
    print("--- Sanitizing config.py ---")
    config_path = staged_root / "config.py"
    content = config_path.read_text(encoding='utf-8')
    pattern = r"def get_db_key\(\) -> str:.*?(?=\ndef|$)"
    replacement = 'def get_db_key() -> str:\n    raise RuntimeError("CRITICAL: Production Key Access Denied.")'
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    config_path.write_text(new_content, encoding='utf-8')

def run_nuitka(staged_root):
    """Runs Nuitka (Linux Optimized) - LGPL Mode."""
    print("--- Compiling with Nuitka (Linux Optimized + LGPL) ---")
    abs_dist = DIST_DIR.resolve()

    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        # NOTE: Plugin disabled to allow manual PySide6 handling for LGPL
        # "--enable-plugin=pyside6",

        # --- Force output filename to match AppRun expectation ---
        "--output-filename=klyve.bin",

        "--include-data-dir=data/templates=data/templates",

        # --- LGPL COMPLIANCE: EXCLUDE QT ---
        "--nofollow-import-to=PySide6",
        "--nofollow-import-to=shiboken6",
        "--nofollow-import-to=google.genai",

        # --- INCLUSIONS (Matching Windows Stability) ---
        "--include-module=master_orchestrator",
        "--include-module=klyve_db_manager",
        "--include-module=llm_service",
        "--include-package=agents",
        "--include-package=gui",
        "--include-module=sqlcipher3",
        "--include-module=sqlite3",
        "--include-module=uuid",
        "--include-module=json",
        "--include-module=logging",
        "--include-module=shutil",
        "--include-module=base64",
        "--include-module=re",
        "--include-module=subprocess",
        "--include-module=threading",
        "--include-module=traceback",
        "--include-module=git",
        "--include-module=gitdb",
        "--include-module=openai",
        "--include-module=anthropic",
        # "--include-module=google.genai",
        "--include-module=replicate",
        "--include-module=requests",
        "--include-module=pandas",
        "--include-module=openpyxl",
        "--include-module=docx",
        "--include-module=htmldocx",
        "--include-module=markdown",
        "--include-module=bs4",
        "--include-module=graphviz",
        "--include-module=plotly",
        "--include-module=kaleido",
        "--include-module=PIL",
        "--include-module=pypdf",

        # --- EXCLUSIONS (Matching Windows Optimization) ---
        "--nofollow-import-to=numba",
        "--nofollow-import-to=llvmlite",
        "--nofollow-import-to=zmq",
        "--nofollow-import-to=IPython",
        "--nofollow-import-to=jupyter",
        "--nofollow-import-to=scipy",
        "--nofollow-import-to=matplotlib",
        "--nofollow-import-to=setuptools",
        "--nofollow-import-to=distutils",
        "--nofollow-import-to=tkinter",

        f"--output-dir={str(abs_dist)}",
        "klyve.py"
    ]

    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=staged_root)
    if result.returncode != 0:
        print("❌ Nuitka compilation failed.")
        sys.exit(1)

def copy_vault_extension(staged_root):
    """Copies the compiled .so vault extension."""
    print("--- Bundling Iron Vault (.so) ---")
    dist_root = DIST_DIR / "klyve.dist"

    # Find compiled Linux extension
    so_files = list(staged_root.glob("vault*.so"))

    if not so_files:
        print("❌ FATAL: Could not find compiled vault.so in staging.")
        sys.exit(1)

    src_so = so_files[0]
    dst_so = dist_root / "vault.so"

    shutil.copy2(src_so, dst_so)
    print(f"✅ Copied {src_so.name} to {dst_so}")

def bundle_linux_dependencies(project_root):
    """Bundles system Graphviz for Linux sidecar."""
    print("--- Bundling Linux Dependencies ---")

    dist_gv_bin = DIST_DIR / "klyve.dist" / "dependencies" / "graphviz" / "bin"
    dist_gv_bin.mkdir(parents=True, exist_ok=True)

    # Locate system dot
    dot_path = shutil.which("dot")
    if dot_path:
        shutil.copy2(dot_path, dist_gv_bin / "dot")
        print(f"✅ Bundled system 'dot' from {dot_path}")
    else:
        print("⚠️ Warning: 'dot' not found on system. Graphviz features may fail.")

def bundle_google_genai(project_root):
    """Manually bundles google.genai to bypass Nuitka compilation hang."""
    print("--- Bundling google.genai (Raw Source) ---")

    try:
        import google.genai
        # Find the actual source directory on disk
        src_path = Path(google.genai.__file__).parent

        # Destination: dist/klyve.dist/google/genai
        dst_path = DIST_DIR / "klyve.dist" / "google" / "genai"

        if dst_path.exists(): shutil.rmtree(dst_path)

        # Copy the package
        shutil.copytree(src_path, dst_path)
        print(f"✅ Copied google.genai from {src_path}")

    except ImportError:
        print("⚠️ Warning: google.genai not found. Build may fail at runtime.")
    except Exception as e:
        print(f"❌ Error bundling google.genai: {e}")
        sys.exit(1)

def bundle_gui_assets(project_root):
    """Copies assets."""
    print("--- Bundling GUI Assets ---")
    src_style = project_root / "gui" / "style.qss"
    src_icons = project_root / "gui" / "icons"
    src_images = project_root / "gui" / "images"
    dist_gui = DIST_DIR / "klyve.dist" / "gui"
    dist_gui.mkdir(exist_ok=True)

    if src_style.exists(): shutil.copy2(src_style, dist_gui / "style.qss")
    if src_icons.exists():
        dst = dist_gui / "icons"
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(src_icons, dst)
    if src_images.exists():
        dst = dist_gui / "images"
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(src_images, dst)

def post_build_cleanup(dist_dir):
    """Replaces Nuitka-bundled Qt with clean system versions for LGPL."""
    print("--- 🧹 Performing LGPL Compliance Setup (Linux) ---")

    src_pyside = CLEAN_PYSIDE_ROOT / "PySide6"
    src_shiboken = CLEAN_PYSIDE_ROOT / "shiboken6"

    dst_pyside = dist_dir / "PySide6"
    dst_shiboken = dist_dir / "shiboken6"

    # Copy PySide6
    if dst_pyside.exists(): shutil.rmtree(dst_pyside)
    if src_pyside.exists():
        shutil.copytree(src_pyside, dst_pyside)
        print(f"✅ Copied clean PySide6 from {src_pyside}")
    else:
        print(f"❌ ERROR: Could not find clean PySide6 at {src_pyside}")
        sys.exit(1)

    # Copy shiboken6
    if dst_shiboken.exists(): shutil.rmtree(dst_shiboken)
    if src_shiboken.exists():
        shutil.copytree(src_shiboken, dst_shiboken)
        print(f"✅ Copied clean shiboken6 from {src_shiboken}")
    else:
        print(f"⚠️ Warning: Could not find clean shiboken6 at {src_shiboken}")

    # Remove conflicting root libraries (Linux uses .so)
    print("--- Cleaning Root Library Conflicts ---")
    for so in dist_dir.glob("libQt6*.so*"):
        try:
            so.unlink()
            print(f"   Removed conflict: {so.name}")
        except: pass

    for so in dist_dir.glob("libshiboken6.so*"):
        try:
            so.unlink()
            print(f"   Removed conflict: {so.name}")
        except: pass

    print("--- LGPL Setup Complete ---")

def main():
    project_root = Path(__file__).parent
    clean_build_env()
    staged_src = stage_project(project_root)

    print("--- Generating Production Vault ---")
    subprocess.run([sys.executable, "tools/build_vault.py"], cwd=staged_src, check=True)

    print("--- Compiling Vault Extension ---")
    subprocess.run([sys.executable, "setup_vault.py", "build_ext", "--inplace"], cwd=staged_src, check=True)

    print("--- Compiling Core Logic ---")
    subprocess.run([sys.executable, "setup_cython.py", "build_ext", "--inplace"], cwd=staged_src, check=True)

    sanitize_config(staged_src)
    run_nuitka(staged_src)
    copy_vault_extension(staged_src)
    bundle_linux_dependencies(project_root)
    bundle_gui_assets(project_root)

    # --- NEW: Bundle the skipped library ---
    bundle_google_genai(project_root)

    # --- NEW: Run LGPL Cleanup ---
    post_build_cleanup(DIST_DIR / "klyve.dist")

    print("\n✨ LINUX BUILD COMPLETE ✨")
    print(f"Artifacts located in: {DIST_DIR / 'klyve.dist'}")

if __name__ == "__main__":
    main()