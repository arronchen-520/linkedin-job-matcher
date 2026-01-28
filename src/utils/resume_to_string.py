import fitz  # PyMuPDF
import re
import logging
import sys
from pathlib import Path
from utils.file_path import RESUME_DIR

def load_resume_pdf(file_name: str, logger: logging.Logger) -> str:
    """
    Loads and extracts text content specifically from a PDF file.
    
    Args:
        file_name (str): The filename of the PDF resume (must be inside RESUME_DIR).
        logger (logging.Logger): The logger instance for recording events.
        
    Returns:
        str: The cleaned, normalized string content of the PDF.
             Returns an empty string if the file is invalid or unreadable.
    """
    path = Path(RESUME_DIR / file_name)
    
    # Validation: Ensure file exists and has the correct extension
    if not path.exists() or path.suffix.lower() != ".pdf":
        logger.error(f"Error: File not found or invalid format (PDF required): {path}")
        return ""  # Return empty string as per docstring, instead of crashing

    try:
        text = ""
        # Open the PDF document
        with fitz.open(path) as doc:
            # Iterate through every page to extract raw text
            for page in doc:
                text += page.get_text() + "\n\n"
        
        # Data Cleaning: Normalize whitespace
        # Collapses multiple newlines/spaces into a single space to reduce LLM token usage.
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    except Exception as e:
        logger.error(f"Critical Error: Failed to read PDF file: {e}")
        return ""