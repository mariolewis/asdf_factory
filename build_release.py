import os
import sys
import shutil
import subprocess
import re
from pathlib import Path

# Configuration
PROJECT_NAME = "Klyve"
MAIN_SCRIPT = "klyve.py"
BUILD_DIR = Path("build_stage")
DIST_DIR = Path("dist")

# --- LGPL CONFIGURATION ---
# We point to the parent 'site-packages' folder so we can grab both PySide6 and shiboken6
# Note: We use the path you provided, stripped back one level to find both folders.
CLEAN_PYSIDE_ROOT = Path(r"E:\Python311\Lib\site-packages")

def clean_build_env():
    """Removes previous build artifacts."""
    print(f"--- Cleaning {BUILD_DIR} and {DIST_DIR} ---")
    if BUILD_DIR.exists():
        try:
            shutil.rmtree(BUILD_DIR)
        except PermissionError:
            print(f"Warning: Could not fully delete {BUILD_DIR}. Is it open?")

    if DIST_DIR.exists():
        try:
            shutil.rmtree(DIST_DIR)
        except PermissionError:
            print(f"Warning: Could not fully delete {DIST_DIR}. Is it open?")

    BUILD_DIR.mkdir(exist_ok=True)

def stage_project(project_root):
    """Copies source code to a staging area to modify it safely."""
    print(f"--- Staging Project to {BUILD_DIR} ---")

    def ignore_patterns(path, names):
        return [n for n in names if n in [
            '.git', '__pycache__', 'venv', 'env',
            'dist', 'build', 'backups', 'tests',
            BUILD_DIR.name,
            '.idea', '.vscode', 'data'
        ]]

    dest_src = BUILD_DIR / "src"
    if dest_src.exists():
        shutil.rmtree(dest_src)

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
    """Reads config.py and REMOVES the get_db_key() function implementation."""
    print("--- Sanitizing config.py (Removing plaintext keys) ---")
    config_path = staged_root / "config.py"
    content = config_path.read_text(encoding='utf-8')

    pattern = r"def get_db_key\(\) -> str:.*?(?=\ndef|$)"
    replacement = 'def get_db_key() -> str:\n    raise RuntimeError("CRITICAL: Attempted to access insecure key in Production Build. Use Vault instead.")'

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    config_path.write_text(new_content, encoding='utf-8')

def run_nuitka(staged_root):
    """Runs the Nuitka compiler with aggressive optimization."""
    print("--- Compiling with Nuitka (LGPL Compliant Mode) ---")

    abs_dist = DIST_DIR.resolve()

    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        # NOTE: Plugin disabled to allow manual PySide6 handling for LGPL
        # "--enable-plugin=pyside6",
        "--include-data-dir=data/templates=data/templates",
        "--windows-icon-from-ico=gui/icons/klyve_logo.ico",

        # Use 'force' for debugging crashes, 'disable' for release
        "--windows-console-mode=disable",

        # --- LGPL COMPLIANCE: EXCLUDE QT ---
        # This forces Nuitka to ignore Qt so we can copy the clean folders manually later
        "--nofollow-import-to=PySide6",
        "--nofollow-import-to=shiboken6",
        "--nofollow-import-to=google.genai",

        # --- INCLUSIONS (Keep Critical Deps) ---
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
        #"--include-module=google.genai",
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

        # --- EXCLUSIONS (Debloat) ---
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

    print(f"Executing Nuitka build...")
    result = subprocess.run(cmd, cwd=staged_root)
    if result.returncode != 0:
        print("❌ Nuitka compilation failed.")
        sys.exit(1)

def copy_vault_extension(staged_root):
    """Manually copies the compiled vault extension."""
    print("--- Bundling Iron Vault ---")
    dist_root = DIST_DIR / "klyve.dist"
    pyd_files = list(staged_root.glob("vault*.pyd")) + list(staged_root.glob("vault*.so"))
    if not pyd_files:
        print("❌ FATAL: Could not find compiled vault extension in staging.")
        sys.exit(1)
    src_pyd = pyd_files[0]
    ext_suffix = src_pyd.suffix
    dst_pyd = dist_root / f"vault{ext_suffix}"
    shutil.copy2(src_pyd, dst_pyd)
    print(f"✅ Copied {src_pyd.name} to {dst_pyd}")

def bundle_google_genai(project_root):
    """
    Manually copies the google.genai package to the dist folder.
    This bypasses the Nuitka compilation hang on google.genai.types.
    """
    print("--- Bundling google.genai (Raw Source) ---")

    # Locate the package in the current environment
    import google.genai
    src_path = Path(google.genai.__file__).parent

    # Destination: dist/klyve.dist/google/genai
    # Note: We must preserve the namespace package structure 'google/genai'
    dst_path = DIST_DIR / "klyve.dist" / "google" / "genai"

    if dst_path.exists():
        shutil.rmtree(dst_path)

    shutil.copytree(src_path, dst_path)
    print(f"✅ Copied google.genai from {src_path}")

def bundle_dependencies(project_root):
    """Copies the Graphviz sidecar."""
    print("--- Bundling Sidecar Dependencies ---")
    src_gv = project_root / "dependencies" / "graphviz"
    dist_gv = DIST_DIR / "klyve.dist" / "dependencies" / "graphviz"
    if not src_gv.exists():
        print("❌ Error: Graphviz dependency not found.")
        sys.exit(1)
    if dist_gv.exists(): shutil.rmtree(dist_gv)
    shutil.copytree(src_gv, dist_gv)
    print(f"✅ Graphviz bundled to {dist_gv}")

def bundle_gui_assets(project_root):
    """Copies non-code GUI assets (styles, icons) to the dist folder."""
    print("--- Bundling GUI Assets ---")
    src_style = project_root / "gui" / "style.qss"
    src_icons = project_root / "gui" / "icons"
    src_images = project_root / "gui" / "images"
    dist_gui = DIST_DIR / "klyve.dist" / "gui"
    dist_gui.mkdir(exist_ok=True)

    if src_style.exists():
        shutil.copy2(src_style, dist_gui / "style.qss")
        print(f"✅ Copied style.qss")

    if src_icons.exists():
        dst_icons = dist_gui / "icons"
        if dst_icons.exists(): shutil.rmtree(dst_icons)
        shutil.copytree(src_icons, dst_icons)
        print(f"✅ Copied icons")

    if src_images.exists():
        dst_images = dist_gui / "images"
        if dst_images.exists(): shutil.rmtree(dst_images)
        shutil.copytree(src_images, dst_images)
        print(f"✅ Copied images")

def post_build_cleanup(dist_dir):
    """Replaces Nuitka-bundled Qt components with clean, swappable versions for LGPL compliance."""
    print("--- 🧹 Performing LGPL Compliance Setup ---")

    # Define source paths (Using the constant defined at top of file)
    src_pyside = CLEAN_PYSIDE_ROOT / "PySide6"
    src_shiboken = CLEAN_PYSIDE_ROOT / "shiboken6"

    # Define destination paths
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
        # Note: Sometimes shiboken is inside PySide6, but usually it's a sibling.
        # If this fails, check your folder structure.
        print(f"⚠️ Warning: Could not find clean shiboken6 at {src_shiboken}")

    # NUKE any root-level Qt DLLs to force loading from the subfolders
    print("--- Cleaning Root DLL Conflicts ---")
    removed_count = 0
    for dll in dist_dir.glob("Qt6*.dll"):
        try:
            dll.unlink()
            print(f"   Removed conflict: {dll.name}")
            removed_count += 1
        except Exception as e:
            print(f"   Failed to remove {dll.name}: {e}")

    # Also clean shiboken6.dll if it leaked into root
    for dll in dist_dir.glob("shiboken6.dll"):
        try:
            dll.unlink()
            print(f"   Removed conflict: {dll.name}")
        except: pass

    if removed_count == 0:
        print("   (No conflicting DLLs found in root - this is good)")

    print("--- LGPL Setup Complete ---")

def generate_sbom(scan_target):
    """
    Generates the SBOM by scanning the final distribution folder.
    Saves it to the project root so Klyve.iss can find it.
    """
    print("--- Generating Windows SBOM ---")
    # Output file stays in project root for Inno Setup
    sbom_path = Path("klyve_sbom.spdx.json").resolve()

    # Scan the target directory (dist/klyve.dist)
    # The scan_target argument passed from main() is already the dist path
    cmd = ["syft", str(scan_target), "-o", f"spdx-json={sbom_path}"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ SBOM generated at: {sbom_path}")
        else:
            print(f"⚠️ SBOM warning: {result.stderr}")
    except Exception as e:
        print(f"❌ SBOM Error: {e}")

def remove_unused_multimedia_dlls(dist_dir):
    """
    Surgically removes unused Qt Multimedia/Image plugins.
    CRITICAL: Does NOT touch 'dependencies/graphviz', which needs tiff/freetype.
    """
    print("--- Security Hardening: Removing unused Qt Binaries ---")

    # 1. Qt Multimedia (Audio/Video) - Safe to remove
    # 2. Qt TIFF Plugin (qtiff.dll) - Safe to remove if app doesn't load TIFFs
    patterns_to_remove = [
        "avcodec-*.dll", "avformat-*.dll", "avutil-*.dll",
        "swresample-*.dll", "swscale-*.dll",
        "Qt6Multimedia.dll", "Qt6MultimediaWidgets.dll",
        "qtiff.dll"
    ]

    removed_count = 0

    # We explicitly look inside the PySide6 folder to be safe
    # This ensures we don't accidentally hit Graphviz in 'dependencies'
    qt_root = dist_dir / "PySide6"

    if not qt_root.exists():
        print(f"⚠️ Warning: PySide6 folder not found at {qt_root}")
        return

    for pattern in patterns_to_remove:
        for dll_path in qt_root.rglob(pattern):
            try:
                dll_path.unlink()
                print(f"   Removed: {dll_path.name}")
                removed_count += 1
            except Exception as e:
                print(f"   ⚠️ Failed to remove {dll_path.name}: {e}")

    print(f"   Removed {removed_count} binaries from Qt.")

def main():
    project_root = Path(__file__).parent
    clean_build_env()
    staged_src = stage_project(project_root)

    print("--- Generating Production Vault ---")
    subprocess.run([sys.executable, "tools/build_vault.py"], cwd=staged_src, check=True)

    print("--- Compiling Vault Extension ---")
    subprocess.run([sys.executable, "setup_cython.py", "build_ext", "--inplace"], cwd=staged_src, check=True)

    # NOTE: We also compile the Vault here to ensure it's ready for copying
    subprocess.run([sys.executable, "setup_vault.py", "build_ext", "--inplace"], cwd=staged_src, check=True)

    sanitize_config(staged_src)
    generate_sbom(project_root)

    # 1. Compile the app (This creates the dist folder)
    run_nuitka(staged_src)

    # 2. Bundle dependencies
    copy_vault_extension(staged_src)
    bundle_dependencies(project_root)
    bundle_gui_assets(project_root)
    bundle_google_genai(project_root)

    # 3. Run LGPL Cleanup
    post_build_cleanup(DIST_DIR / "klyve.dist")

    # 4. REMOVE: Security Hardening (Delete vulnerable DLLs)
    remove_unused_multimedia_dlls(DIST_DIR / "klyve.dist")

    # 5. GENERATE: SBOM (Scan the final, clean folder)
    # Note: We scan the DIST folder now, not the project root, to be accurate
    generate_sbom(DIST_DIR / "klyve.dist")

    print("\n✨ BUILD COMPLETE ✨")
    print(f"Artifacts located in: {DIST_DIR / 'klyve.dist'}")

if __name__ == "__main__":
    main()