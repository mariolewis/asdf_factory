# agents/agent_codebase_scanner.py

import logging
import time
import hashlib
import threading
import uuid
import os
from datetime import datetime, timezone
from pathlib import Path
from llm_service import LLMService
from klyve_db_manager import KlyveDBManager
from agents.agent_code_summarization import CodeSummarizationAgent
from agents.doc_update_agent_rowd import DocUpdateAgentRoWD

class CodebaseScannerAgent:
    """
    Agent responsible for scanning a local codebase, summarizing each file,
    and populating the Record-of-Work-Done (RoWD) in the database.
    """

    def __init__(self, llm_service: LLMService, db_manager: KlyveDBManager):
        if not llm_service:
            raise ValueError("llm_service is required for the CodebaseScannerAgent.")
        if not db_manager:
            raise ValueError("db_manager is required for the CodebaseScannerAgent.")
        self.llm_service = llm_service
        self.db_manager = db_manager
        self.summarization_agent = CodeSummarizationAgent(self.llm_service)
        self.doc_update_agent = DocUpdateAgentRoWD(self.db_manager, self.llm_service)
        logging.info("CodebaseScannerAgent initialized.")

    def scan_project(self, project_id: str, root_path_str: str, pause_event: threading.Event, progress_callback, worker_instance):
        """
        Scans a project directory, processes each file, and saves the summary,
        emitting structured progress updates.
        """
        logging.info(f"--- CodebaseScannerAgent: scan_project starting ---")
        logging.info(f"Received root_path_str for scanning: '{root_path_str}'")

        root_path = Path(root_path_str)
        source_extensions = [
            # Python
            '.py', '.pyw', '.pyx', '.pyi',  # .pyi = type stubs

            # JavaScript/TypeScript
            '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',

            # Web Front-End
            '.html', '.htm', '.xhtml',
            '.css', '.scss', '.sass', '.less',
            '.vue', '.svelte', '.astro',

            # Java/JVM Languages
            '.java', '.kt', '.kts', '.scala', '.groovy', '.clj', '.cljs',

            # C/C++
            '.c', '.h', '.cpp', '.cc', '.cxx', '.hpp', '.hxx', '.hh',

            # C#/.NET
            '.cs', '.vb', '.fs', '.fsx',  # F#

            # Go
            '.go',

            # Rust
            '.rs',

            # PHP
            '.php', '.php3', '.php4', '.php5', '.phtml',

            # Ruby
            '.rb', '.rake', '.gemspec',

            # Swift/Objective-C
            '.swift', '.m', '.mm',

            # Mobile Development
            '.dart',  # Flutter
            '.kt', '.kts',  # Kotlin (Android)

            # Python Data Science
            '.ipynb',  # Jupyter notebooks (JSON format but contains code)

            # Shell Scripting
            '.sh', '.bash', '.zsh', '.fish', '.ksh',
            '.ps1', '.psm1',  # PowerShell
            '.bat', '.cmd',  # Windows batch

            # Data/Scientific Computing
            '.r', '.R', '.Rmd',  # R and R Markdown
            '.jl',  # Julia
            '.mat', '.m',  # MATLAB (conflict with Objective-C, context-dependent)

            # Functional Languages
            '.hs', '.lhs',  # Haskell
            '.ml', '.mli',  # OCaml
            '.ex', '.exs',  # Elixir
            '.erl', '.hrl',  # Erlang
            '.elm',  # Elm
            '.scm', '.rkt',  # Scheme/Racket
            '.lisp', '.lsp', '.cl', '.el',  # Lisp variants

            # Systems Programming
            '.zig',  # Zig
            '.nim',  # Nim
            '.v',  # V or Verilog (context-dependent)
            '.d',  # D
            '.ada', '.adb', '.ads',  # Ada
            '.asm', '.s', '.nasm',  # Assembly

            # Lua
            '.lua',

            # Perl
            '.pl', '.pm', '.t', '.pod',

            # Database/Query Languages
            '.sql', '.psql', '.plsql', '.pls',
            '.hql',  # Hive
            '.pig',  # Pig Latin
            '.cql',  # Cassandra/Cypher
            '.cypher',  # Neo4j

            # Web Backend/Templates
            '.jsp', '.jspx',  # Java Server Pages
            '.asp', '.aspx', '.ascx',  # ASP.NET
            '.erb',  # Ruby ERB
            '.ejs',  # EJS templates
            '.hbs', '.handlebars',  # Handlebars
            '.pug', '.jade',  # Pug templates
            '.jinja', '.jinja2', '.j2',  # Jinja
            '.twig',  # Twig (PHP)
            '.blade.php',  # Laravel Blade
            '.eex', '.leex', '.heex',  # Elixir templates
            '.mustache',  # Mustache templates

            # Enterprise/Business
            '.cls', '.trigger', '.apex', '.page', '.component',  # Salesforce
            '.abap',  # SAP
            '.sas',  # SAS
            '.do', '.ado',  # Stata

            # Configuration as Code (contains logic)
            '.tf', '.tfvars',  # Terraform
            '.bicep',  # Azure Bicep
            '.pp',  # Puppet
            '.gradle',  # Gradle (Groovy)
            '.sbt',  # SBT (Scala)

            # Data Pipeline/Workflow
            '.nf',  # Nextflow
            '.wdl',  # Workflow Description Language
            '.cwl',  # Common Workflow Language
            '.snakefile',  # Snakemake

            # Schema/Protocol Definitions (contain structure logic)
            '.proto',  # Protocol Buffers
            '.graphql', '.gql',  # GraphQL
            '.prisma',  # Prisma ORM
            '.avdl',  # Avro IDL
            '.thrift',  # Apache Thrift

            # Hardware Description Languages
            '.vhd', '.vhdl',  # VHDL
            '.v', '.sv',  # Verilog/SystemVerilog

            # Game Development
            '.gd',  # Godot (GDScript)
            '.shader',  # Shader files
            '.glsl', '.hlsl', '.cg',  # Shader languages

            # Markup with Code (contains embedded logic)
            '.xaml',  # XAML (can contain binding logic)
            '.qml',  # Qt QML

            # Fortran
            '.f', '.for', '.f90', '.f95', '.f03', '.f08',

            # Pascal/Delphi
            '.pas', '.pp', '.dpr',

            # Tcl
            '.tcl',

            # AWK
            '.awk',

            # Makefile (contains build logic)
            '.mk', 'Makefile', 'makefile', 'GNUmakefile',

            # CMake
            '.cmake', 'CMakeLists.txt',

            # UI Definition Files (Qt, Android)
            '.ui',  # Qt Designer
            '.qrc',  # Qt Resources

            # Miscellaneous
            '.coffee',  # CoffeeScript
            '.ts',  # TypeScript (already listed)
            '.jsonnet',  # Jsonnet (generates config but is code)
            '.dhall',  # Dhall
            '.nix',  # Nix expressions
        ]

        all_files = []
        try:
            if not os.path.exists(root_path_str):
                error_msg = f"The provided directory does not exist: {root_path_str}"
                logging.error(error_msg)
                progress_callback(("ERROR", error_msg))
                return False

            for dirpath, dirnames, filenames in os.walk(root_path_str):
                for filename in filenames:
                    # Construct a Path object for robust suffix checking and path manipulation
                    file_path = Path(dirpath) / filename
                    if file_path.suffix.lower() in source_extensions:
                        all_files.append(file_path)
        except Exception as e:
            logging.error(f"An unexpected error occurred during os.walk: {e}", exc_info=True)
            return False

        total_files = len(all_files)
        logging.info(f"Found {total_files} source files to analyze using os.walk.")
        progress_callback(("SCANNING", {"total_files": total_files}))

        for i, file_path in enumerate(all_files):
            if worker_instance.is_cancelled:
                logging.warning("Cancellation signal received. Aborting scan.")
                return False

            if pause_event.is_set():
                logging.info(f"Analysis paused at file {i+1}/{total_files}.")
                pause_event.wait()
                logging.info("Analysis resumed.")

            relative_path_str = str(file_path.relative_to(root_path)).replace('\\', '/')

            progress_callback(("SUMMARIZING", {"total": total_files, "current": i + 1, "filename": relative_path_str}))

            existing_artifact = self.db_manager.get_artifact_by_path(project_id, relative_path_str)
            if existing_artifact and existing_artifact['code_summary']:
                logging.info(f"Skipping already summarized file: {relative_path_str}")
                continue

            try:
                content = file_path.read_text(encoding='utf-8')
                summary = "Qt Designer UI file." if file_path.suffix.lower() == '.ui' else self.summarization_agent.summarize_code(content)
                if "Error:" in summary:
                    logging.warning(f"Could not generate summary for {relative_path_str}. Skipping.")
                    continue

                file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
                artifact_data = {
                    "artifact_id": f"art_{uuid.uuid4().hex[:8]}",
                    "project_id": project_id,
                    "file_path": relative_path_str,
                    "artifact_name": file_path.name,
                    "artifact_type": "EXISTING_CODE",
                    "code_summary": summary,
                    "file_hash": file_hash,
                    "status": "ANALYZED",
                    "last_modified_timestamp": datetime.now(timezone.utc).isoformat(),
                }
                self.db_manager.add_brownfield_artifact(artifact_data)

            except Exception as e:
                logging.error(f"Failed to process file {relative_path_str}: {e}")

        logging.info("Codebase scan and summarization complete.")
        return True