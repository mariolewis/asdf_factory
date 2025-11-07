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

# Create a persistent temp directory for this session
TEMP_IMAGE_DIR = Path(tempfile.gettempdir()) / "asdf_session_images"
TEMP_IMAGE_DIR.mkdir(exist_ok=True)

def _cleanup_temp_images():
    """Remove temp images on application exit."""
    try:
        for f in TEMP_IMAGE_DIR.glob("*.png"):
            os.remove(f)
    except Exception as e:
        logging.warning(f"Could not clean up temp images: {e}")

atexit.register(_cleanup_temp_images)

def generate_mermaid_png(mermaid_text: str) -> BytesIO:
    """
    Creates a PNG from a Mermaid.js text block using the mermaid.ink API.
    This avoids any local browser/Node.js dependency.
    """
    try:
        # 1. Encode the Mermaid text for the URL
        # We use a standard base64 encoding
        mermaid_bytes = mermaid_text.encode("utf-8")
        base64_bytes = base64.urlsafe_b64encode(mermaid_bytes)
        base64_string = base64_bytes.decode("utf-8")

        # 2. Call the public API
        url = f"[https://mermaid.ink/img/](https://mermaid.ink/img/){base64_string}"
        response = requests.get(url, timeout=10)

        # 3. Check for success and return the image bytes
        if response.status_code == 200:
            logging.debug("Successfully rendered Mermaid diagram via mermaid.ink")
            return BytesIO(response.content)
        else:
            logging.error(f"mermaid.ink API failed with status {response.status_code}: {response.text}")
            raise Exception(f"mermaid.ink API failed: {response.status_code}")

    except Exception as e:
        logging.error(f"Failed to generate Mermaid PNG via API: {e}")
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
    Scans Markdown for Mermaid blocks and wraps them in a <pre>
    block for clean on-screen display, avoiding failed render attempts.
    """
    import re
    def wrap_in_pre(match):
        mermaid_text = match.group(1)
        # Wrap the text in a <pre> block with some simple styling
        return f"""
<pre style="background-color: #2b2b2b; color: #f1f1f1; padding: 10px; border-radius: 5px;">
<b>--- Mermaid Diagram ---</b>
{html.escape(mermaid_text)}
</pre>
"""

    # Regex to find ```mermaid ... ``` blocks
    pattern = re.compile(r"```mermaid\s*(.*?)```", re.DOTALL)
    processed_markdown = re.sub(pattern, wrap_in_pre, markdown_text)
    return processed_markdown