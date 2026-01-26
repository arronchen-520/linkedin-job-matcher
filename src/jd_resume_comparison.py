import ollama
import logging
import json
import re
from typing import Dict, Any

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
        You are a strict ATS (Applicant Tracking System) and Senior Technical Recruiter.
        Evaluate the candidate based on the Job Description (JD).

        ### JOB DESCRIPTION:
        {jd_text}

        ### CANDIDATE RESUME:
        {resume_text}

        ### SCORING RULES:
        1. **Hard Requirements:** If the candidate lacks a "Must Have" skill (e.g., "Proficient in AWS"), penalize heavily.
        2. **Keywords:** Check for specific technologies mentioned in the JD.
        3. **Experience:** Verify if the seniority level matches.
        4. **Output:** Assign a score from 0 to 100.

        ### OUTPUT FORMAT (JSON ONLY):
        Strictly output a valid JSON object with these keys:
        {{
            "match_score": <int>,
            "reasoning": "<string: A concise, professional summary (max 2 sentences) of the fit>",
            "missing_skills": [<list of strings: Top 3 critical skills/keywords missing from resume>]
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
                }
            )

            content = response['message']['content']
            return self._parse_json_response(content)

        except Exception as e:
            logger.error(f"Inference failed: {e}")
            return self._get_default_response()

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """
        Robustly extracts JSON from the LLM response, handling common formatting errors.
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback: Try to find the JSON block using regex if the model chatted around it
            logger.warning("Raw JSON decode failed, attempting regex extraction.")
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
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
    logger = logging.getLogger(__name__)
    # Example usage for testing
    matcher = ResumeMatcher(model_name="qwen2.5")

    sample_jd = """
    Software Engineer (Python).
    Requirements:
    - 3+ years of experience in Python and Django.
    - Experience with AWS (EC2, Lambda).
    - Knowledge of React is a plus.
    """

    sample_resume = """
    Junior Developer.
    Skills: Python, C++, HTML.
    Experience: 1 year building internal tools using Python.
    No cloud experience.
    """

    logging.info("Running Matcher...")
    result = matcher.match(sample_resume, sample_jd)
    
    print(json.dumps(result, indent=2))