# In gui/rendering_utils.py
import logging
import subprocess
import tempfile
import atexit
import os
import html
import re
import base64
import requests
from pathlib import Path
from io import BytesIO
import graphviz

# Create a persistent temp directory for this session
TEMP_IMAGE_DIR = Path(tempfile.gettempdir()) / "asdf_session_images"
TEMP_IMAGE_DIR.mkdir(exist_ok=True)

def _cleanup_temp_images():
    """Remove temp images on application exit."""
    try:
        for f in TEMP_IMAGE_DIR.glob("*.png"):
            if f.exists():
                os.remove(f)
    except Exception as e:
        logging.warning(f"Could not clean up temp images: {e}")

atexit.register(_cleanup_temp_images)

def generate_dot_png(dot_text: str) -> BytesIO:
    """
    Creates a PNG from a Graphviz DOT text block.
    """
    try:
        # Create a Graphviz object from the DOT source
        # We specify 'png' as the format and get the raw bytes
        png_data = graphviz.Source(dot_text).pipe(format='png')

        if not png_data:
            raise Exception("Graphviz returned empty image data.")

        logging.debug("Successfully rendered DOT diagram via Graphviz")
        return BytesIO(png_data)

    except graphviz.backend.execute.CalledProcessError as e:
        # This error means the 'dot' command failed.
        # Check if the stderr indicates a syntax error, or if the executable was truly not found.
        stderr_output = e.stderr.decode('utf-8') if e.stderr else ""
        if "syntax error" in stderr_output:
            error_msg = f"Graphviz (dot) failed due to a syntax error in the generated DOT code.\nError: {stderr_output}"
        else:
            error_msg = f"Graphviz (dot) executable not found or failed. Please ensure Graphviz is installed and in your system's PATH.\nError: {e}"

        logging.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        logging.error(f"Failed to generate DOT PNG: {e}")
        raise

def generate_plotly_png(plotly_fig) -> BytesIO:
    """
    Creates a PNG from a Plotly figure object using kaleido.
    This is the correct way to use kaleido.
    """
    try:
        # Use plotly's built-in kaleido integration
        image_bytes = plotly_fig.to_image(format="png", engine="kaleido")
        return BytesIO(image_bytes)
    except ValueError as e:
        if "kaleido" in str(e):
             logging.error("FATAL: 'kaleido' binary not found. Please install with 'pip install kaleido'.")
             raise Exception("'kaleido' binary not found. Please install with 'pip install kaleido'.")
        else:
            logging.error(f"Failed to render Plotly fig: {e}")
            raise
    except Exception as e:
        logging.error(f"Error during Plotly to PNG conversion: {e}")
        raise

def preprocess_markdown_for_display(markdown_text: str) -> str:
    """
    Scans Markdown for DOT blocks, renders them as images,
    and replaces the block with an <img> tag.
    """
    import re

    def render_dot_block(match):
        dot_text = match.group(1)
        try:
            # Generate the PNG data
            image_bytes_io = generate_dot_png(dot_text)

            # Save to a unique temp file
            img_hash = hash(dot_text)
            img_path = TEMP_IMAGE_DIR / f"dot_{img_hash}.png"
            with open(img_path, "wb") as f:
                f.write(image_bytes_io.getbuffer())

            # Return an <img> tag pointing to the temp file
            # Use Path.as_uri() to get the correct 'file:///' format
            img_src = img_path.as_uri()
            return f'<img src="{img_src}" alt="DOT Diagram">'

        except Exception as e:
            logging.error(f"Failed to render DOT block for GUI: {e}")
            # Fallback to displaying the code
            return f"""
<pre style="background-color: #2b2b2b; color: #CC7832; padding: 10px; border-radius: 5px;">
<b>--- DOT Diagram (Render Failed) ---</b>
{html.escape(dot_text)}
<br><b>Error:</b> {html.escape(str(e))}
</pre>
"""

    # Regex to find ```dot ... ``` blocks
    pattern = re.compile(r"```dot\s*(.*?)```", re.DOTALL)
    processed_markdown = re.sub(pattern, render_dot_block, markdown_text)
    return processed_markdown