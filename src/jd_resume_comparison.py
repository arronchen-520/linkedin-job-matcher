import ollama
import logging
import json
import numpy as np
import re
from utils.logger import setup_logging
from typing import Dict, Any
from utils.file_path import FILTERED_FILE_PATH
from pathlib import Path
import pandas as pd
from utils.resume_to_string import load_resume_pdf



class ResumeMatcher:
    def __init__(self, model_name: str = "qwen2.5"):
        """
        Initializes the ResumeMatcher with a specific LLM model.
        
        Args:
            model_name (str): The Ollama model tag to use (default: "qwen2.5").
        """
        self.model = model_name

    def match(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        """
        Analyzes the alignment between a resume and a job description.

        Args:
            resume_text (str): Plain text content of the resume.
            jd_text (str): Plain text content of the job description.

        Returns:
            dict: A dictionary containing:
                - match_score (int): 0-100
                - reasoning (str): Brief explanation
                - missing_skills (list): Key missing requirements
        """
        # 1. Validation & Truncation
        # We truncate to ~12k characters to ensure we fit within standard context windows
        # while keeping the most relevant info (header, skills, recent exp).
        if not resume_text or not jd_text:
            logger.warning("Empty resume or JD provided.")
            return self._get_default_response()

        # 2. The ATS Prompt
        prompt = f"""
            Role: You are a cynical and strict Hiring Manager. Your goal is to FILTER OUT candidates who are not a perfect match. 
            Do not be polite. Do not hallucinate skills. 
            
            Task: Analyze the fit between the Candidate's Resume and the Job Description (JD).

            ### JOB DESCRIPTION:
            {jd_text}

            ### CANDIDATE RESUME:
            {resume_text}

            ### STRICT SCORING RUBRIC (0-100):
            - **100**: Perfect match. Has ALL skills, exact years of experience, and domain knowledge.
            - **80-99**: Great match. Missing only trivial/nice-to-have skills.
            - **60-79**: Good match. Has core tech stack but lacks domain specific knowledge or slightly under-qualified.
            - **40-59**: Weak match. Missing a KEY requirement (e.g., JD asks for Java/C++, candidate only knows Python; or JD is Senior, candidate is Junior).
            - **0-39**: Mismatch. Role is completely different (e.g., Front-end dev vs Data Scientist).

            ### CRITICAL INSTRUCTION:
            If the JD requires specific heavy engineering skills (e.g., "C++", "Java", "Distributed Systems", "Kubernetes", "React") and the resume is primarily "Data Science/ML" oriented without these explicit engineering skills, **the score MUST be below 50**.
            
            ### OUTPUT FORMAT (JSON ONLY):
            {{
                "match_score": <int>,
                "reasoning": "<string: Brutally honest assessment. Start with the biggest GAP.>",
                "missing_skills": [<list of strings: Top 3 critical missing hard skills>]
            }}
            """

        try:
            # 3. Inference
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                format='json',  # Forces structured output
                options={
                    'temperature': 0.1,  # Low temp for deterministic, consistent scoring
                    'num_ctx': 8192
                }
            )

            content = response['message']['content']
            return json.loads(content)

        except Exception as e:
            logger.error(f"Inference failed: {e}")
            return self._get_default_response()

    def _get_default_response(self) -> Dict[str, Any]:
        """Returns a safe default object in case of errors."""
        return {
            "match_score": 0,
            "reasoning": "Error processing data",
            "missing_skills": []
        }

# ================= MAIN EXECUTION (Example) =================
if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    matcher = ResumeMatcher(model_name="qwen2.5")
    # Convert pdf to text
    resume = load_resume_pdf('Arron Chen Resume 2025 Updated.pdf', logger = logger)
    filename = '20260125_Arron_Machine Learning_filtered.csv'
    path = Path(FILTERED_FILE_PATH/filename)
    df = pd.read_csv(path, encoding='latin1') # 可能要改
    df[['Match Score', 'Reasoning', 'Missing Skills']] = df['Job Description'].apply(lambda x: pd.Series(matcher.match(resume,x)))
    df['Recommend Apply'] = np.where(df['Match Score'] >= 70, True, False)
    df = df[['Job Title', 'Company', 'Posted Ago', 'Min Salary', 'Max Salary', 'Recommend Apply', 'Match Score', 'Reasoning', 'Missing Skills', 'URL', 'Posted Time', 'Salary', 'Reposted', 'Job Description']]
    df.to_csv(path, index = False)
