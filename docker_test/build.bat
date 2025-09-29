@echo off
REM Expert Build Script for proj_3dd8d3ed - Windows Environment
REM This script prepares the environment, creates the required source file, and executes/verifies the application.

SET PYTHON_SOURCE=main_output.py
SET PYTHON_EXECUTABLE=python.exe

ECHO Starting build and verification process for %PYTHON_SOURCE%...

REM --- STEP 1: Ensure Python 3.10+ is installed and accessible via PATH ---
%PYTHON_EXECUTABLE% --version > NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Python executable not found or not in PATH.
    ECHO Please ensure Python 3.10+ is installed and configured correctly (Add Python to PATH).
    EXIT /B 1
)
ECHO Python environment verified.

REM --- STEP 2: Create the source file (main_output.py) based on specification ---

ECHO # main_output.py > %PYTHON_SOURCE%
ECHO import sys >> %PYTHON_SOURCE%
ECHO. >> %PYTHON_SOURCE%
ECHO try: >> %PYTHON_SOURCE%
ECHO     print("Hello World!") >> %PYTHON_SOURCE%
ECHO     sys.exit(0) >> %PYTHON_SOURCE%
ECHO except Exception as e: >> %PYTHON_SOURCE%
ECHO     sys.exit(1) >> %PYTHON_SOURCE%
ECHO Source file created successfully: %PYTHON_SOURCE%

REM --- STEP 3: Execute and Verify (Acceptance Criteria AC-002, AC-003) ---
ECHO.
ECHO Running application... (Expected output: Hello World!)
%PYTHON_EXECUTABLE% %PYTHON_SOURCE%

REM Capture exit code
SET LAST_EXIT_CODE=%ERRORLEVEL%

ECHO.
IF %LAST_EXIT_CODE% EQU 0 (
    ECHO SUCCESS: Application completed successfully. Exit code: %LAST_EXIT_CODE%
    REM Cleanup temporary source file
    DEL %PYTHON_SOURCE%
    EXIT /B 0
) ELSE (
    ECHO FAILURE: Application exited with non-zero exit code: %LAST_EXIT_CODE%
    DEL %PYTHON_SOURCE%
    EXIT /B 1
)
