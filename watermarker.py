import os

def get_comment_syntax(file_extension):
    """
    Returns (start_comment, end_comment).
    Returns None if the file type is not supported for watermarking.
    """
    # Hash-style comments
    hash_style = {
        '.py', '.sh', '.yaml', '.yml', '.rb', '.pl', '.dockerfile', '.conf',
        '.gitignore', '.r', '.jl', '.ps1', '.psm1', '.toml', '.ini', '.env',
        '.editorconfig', '.properties', '.rake', '.gemspec', '.coffee', '.tcl',
        '.awk', '.sed', '.pyx', '.bzl', '.cfg',  # Airflow config
        '.tf', '.tfvars',  # Terraform (also supports //)
        '.wdl', '.cwl',  # Workflow languages
        '.graphql', '.gql',  # GraphQL schemas
        '.ex', '.exs',  # Elixir
        '.nim'  # Nim language
    }

    # Double-slash style (C-family, JS, etc.)
    slash_style = {
        '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs', '.php',
        '.swift', '.dart', '.jsx', '.tsx', '.m', '.mm', '.scala', '.kt',
        '.kts', '.groovy', '.gradle', '.jsonc', '.proto',
        '.sbt',  # Scala Build Tool
        '.cql',  # Cassandra/Neo4j (Cypher also uses //)
        '.cypher',  # Neo4j Cypher
        '.nf',  # Nextflow
        '.jsonnet',  # Jsonnet config
        '.prisma',  # Prisma ORM
        '.svelte',  # Svelte (JS section uses //)
        '.astro',  # Astro framework
        '.cls', '.trigger', '.page',  # Salesforce Apex/Visualforce
        '.apex',  # Salesforce Apex
        '.zig',  # Zig language
        '.v',  # V language
        '.d'  # D language
    }

    # HTML/XML style
    xml_style = {
        '.html', '.xml', '.aspx', '.jsp', '.vue', '.csproj', '.user',
        '.svg', '.xaml', '.xhtml', '.config', '.nuspec', '.pom', '.fsproj',
        '.vbproj', '.md',  # Markdown supports HTML comments
        '.component'  # Salesforce Lightning components
    }

    # CSS style (block comments)
    css_style = {
        '.css', '.scss', '.sass', '.less', '.qss',
        '.sas',  # SAS programming
        '.do', '.ado'  # Stata
    }

    # SQL style (double dash)
    sql_style = {
        '.sql', '.psql', '.hql', '.pig',  # Pig Latin
        '.presto',  # Presto SQL
        '.sf'  # Snowflake (also supports //)
    }

    # PL/SQL uses different comment (though -- also works)
    plsql_style = {
        '.plsql', '.pls', '.pck'
    }

    # Batch files
    bat_style = {
        '.bat', '.cmd'
    }

    # Lisp family (semicolon)
    lisp_style = {
        '.lisp', '.el', '.clj', '.cljs', '.scm', '.rkt'
    }

    # Lua (double dash)
    lua_style = {
        '.lua'
    }

    # Haskell (double dash)
    haskell_style = {
        '.hs', '.lhs', '.dhall'  # Dhall config language
    }

    # Erlang (percent)
    erlang_style = {
        '.erl', '.hrl'
    }

    # MATLAB/Octave (percent)
    matlab_style = {
        '.mat'  # Use .mat to avoid conflict with Objective-C .m
    }

    # Assembly (semicolon)
    asm_style = {
        '.asm', '.s', '.nasm'
    }

    # Fortran (exclamation)
    fortran_style = {
        '.f', '.f90', '.f95', '.f03', '.f08', '.for'
    }

    # Visual Basic (apostrophe)
    vb_style = {
        '.vb', '.vbs', '.bas'
    }

    # LaTeX (percent)
    latex_style = {
        '.tex', '.sty', '.cls', '.bib'
    }

    # Jinja templates (special block comment syntax)
    jinja_style = {
        '.jinja', '.jinja2', '.j2'
    }

    # Elixir templates (special syntax)
    eex_style = {
        '.eex', '.leex', '.heex'
    }

    # ABAP (SAP - uses double quotes)
    abap_style = {
        '.abap'
    }

    ext = file_extension.lower()

    if ext in hash_style:
        return "# ", ""
    elif ext in slash_style:
        return "// ", ""
    elif ext in xml_style:
        return "<!-- ", " -->"
    elif ext in css_style:
        return "/* ", " */"
    elif ext in sql_style or ext in plsql_style:
        return "-- ", ""
    elif ext in bat_style:
        return "REM ", ""
    elif ext in lisp_style or ext in asm_style:
        return "; ", ""
    elif ext in lua_style or ext in haskell_style:
        return "-- ", ""
    elif ext in erlang_style or ext in matlab_style or ext in latex_style:
        return "% ", ""
    elif ext in fortran_style:
        return "! ", ""
    elif ext in vb_style:
        return "' ", ""
    elif ext in jinja_style:
        return "{# ", " #}"
    elif ext in eex_style:
        return "<%# ", " %>"
    elif ext in abap_style:
        return "\" ", ""
    elif ext == '.txt':
        return "", ""  # Special case: No comment syntax, just append text
    else:
        return None  # UNKNOWN/BINARY TYPE - DO NOT TOUCH

def generate_watermark(filename):
    # Handle Dockerfiles without extensions
    if os.path.basename(filename).lower() == 'dockerfile':
        syntax = ("# ", "")
    else:
        _, ext = os.path.splitext(filename)
        syntax = get_comment_syntax(ext)

    # If syntax is None, this is a binary or unknown file. Abort.
    if syntax is None:
        return None

    start_tag, end_tag = syntax
    watermark_text = "Generated by Klyve AI Automated Software Factory"

    return f"\n\n{start_tag}{watermark_text}{end_tag}\n"

def apply_watermark(file_path):
    try:
        if not os.path.exists(file_path):
            return

        # Check if we should watermark this file type at all
        watermark = generate_watermark(file_path)
        if watermark is None:
            return  # Safety exit for binary files

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if "Generated by Klyve" in content:
            return

        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(watermark)

    except Exception as e:
        # Silently fail or log error, but don't crash the main app
        print(f"Watermark skipped for {file_path}: {e}")