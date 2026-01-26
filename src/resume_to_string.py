import fitz  # PyMuPDF
import docx
import os
import re
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResumeLoader:
    """
    A utility class to load text content from PDF and DOCX files.
    """

    @staticmethod
    def load(file_path: str) -> str:
        """
        Detects file type and extracts text accordingly.
        
        Args:
            file_path (str): Path to the resume file.
            
        Returns:
            str: Cleaned text content of the file.
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return ""

        extension = path.suffix.lower()

        try:
            if extension == ".pdf":
                return ResumeLoader._read_pdf(path)
            elif extension in [".docx", ".doc"]:
                return ResumeLoader._read_docx(path)
            elif extension == ".txt":
                return path.read_text(encoding='utf-8')
            else:
                logger.warning(f"Unsupported file format: {extension}")
                return ""
        except Exception as e:
            logger.error(f"Failed to load file {file_path}: {e}")
            return ""

    @staticmethod
    def _read_pdf(path: Path) -> str:
        """Extracts text from PDF using PyMuPDF."""
        text = ""
        with fitz.open(path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
        return ResumeLoader._clean_text(text)

    @staticmethod
    def _read_docx(path: Path) -> str:
        """Extracts text from DOCX using python-docx."""
        doc = docx.Document(path)
        # Join paragraphs with a newline
        text = "\n".join([para.text for para in doc.paragraphs])
        return ResumeLoader._clean_text(text)

    @staticmethod
    def _clean_text(raw_text: str) -> str:
        """
        Cleans the extracted text to normalize whitespace.
        This reduces token usage for the LLM.
        """
        if not raw_text:
            return ""
        
        # Replace multiple newlines with a single newline
        text = re.sub(r'\n+', '\n', raw_text)
        # Replace multiple spaces with a single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

# ================= Integration Example =================
if __name__ == "__main__":
    # 1. Import your Matcher (Assuming it's in a file named resume_matcher.py)
    # from resume_matcher import ResumeMatcher 
    
    # For demo purposes, I will mock the matcher usage here
    print("--- 1. Loading Resume ---")
    
    # Replace this with your actual file path
    my_resume_path = "path/to/my_cv.pdf" 
    
    # Check if file exists to avoid crashing the demo if you copy-paste this
    if not os.path.exists(my_resume_path):
        # Create a dummy file for testing logic
        print("Test file not found, creating a dummy requirements.txt for demo...")
        with open("dummy_resume.txt", "w") as f:
            f.write("I am a Python expert with AWS experience.")
        my_resume_path = "dummy_resume.txt"

    # LOAD THE TEXT
    resume_text = ResumeLoader.load(my_resume_path)
    
    print(f"\n[Extracted Text Preview]:\n{resume_text[:200]}...\n")
    
    if resume_text:
        print("--- 2. Matching with JD ---")
        
        # Define a sample JD
        job_description = "Looking for a Python expert with AWS knowledge."
        
        # Initialize your matcher (from previous step)
        # matcher = ResumeMatcher(model_name="qwen2.5")
        # result = matcher.match(resume_text, job_description)
        
        # print(json.dumps(result, indent=2))
        print("(Matcher would run here and return JSON score)")