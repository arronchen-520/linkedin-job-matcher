import ollama
import logging
import json
import time
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any
from utils.logger import setup_logging
from utils.file_path import FILTERED_FILE_PATH
from utils.resume_to_string import load_resume_pdf

class LocalLLMMatcher:
    """
    A local matching engine powered by Ollama. 
    Serves as a high-privacy fallback to API-based models, running entirely 
    on local hardware (e.g., RTX 3080).
    """

    def __init__(self, model_name: str = "gemma3:12b"):
        """
        Initializes the LocalLLMMatcher with a specific Ollama model.

        Args:
            model_name (str): The name/tag of the local Ollama model to use.
        """
        self.model = model_name
        self.logger = logging.getLogger(__name__)

    def _get_default_response(self) -> Dict[str, Any]:
        """
        Returns a safe default response in case of inference failure.

        Returns:
            dict: Default structure with score 0.
        """
        return {
            "match_score": 0,
            "reasoning": "Error processing data during local inference.",
            "missing_skills": []
        }

    def _evaluate_match(self, resume_text: str, jd_text: str) -> dict:
        """
        Executes the matching logic using the local Ollama instance.
        
        Args:
            resume_text (str): Content of the candidate's resume.
            jd_text (str): Content of the job description.

        Returns:
            dict: Evaluation results containing score, reasoning, and skills.
        """
        if not resume_text or not jd_text:
            self.logger.warning("Empty resume or JD provided.")
            return self._get_default_response()

        # The Prompt remains untouched as per requirements
        prompt = f"""
        ### ROLE:
        You are an elite Technical Talent Acquisition Specialist with 20 years of experience. Be extremely skeptical: prioritize verifiable impact and evidence over keyword lists or self-claims. 
        False positives (bad candidate high score) cost 3x more than false negatives. Filter ruthlessly. Give a final score of 85+ if and only if the candidate meets all the critical skills. 

        ### EVALUATION STEPS (think step-by-step internally, do NOT output these steps):
        1. Parse the JD: Identify CRITICAL must-haves (core tech stack, years of experience, domain) vs SUPPORTING (nice-to-haves).
        2. Extract candidate's effective years of experience. If candidate's years < JD requirement - 2 years (or >30% shortfall), cap match_score at 50.
        3. For each CRITICAL skill/tool: Check if resume shows clear professional/project evidence of usage (specific achievements, outcomes, complexity). No evidence → cap match_score at 50.
        4. Evaluate supporting skills only if criticals are met. Give credit only for demonstrated context (how/where used), not mere mentions.
        5. Anti-assumption: Do not infer unstated expertise (e.g., no "Python → FastAPI"). Ignore protected attributes (name, gender, location, etc.).
        6. Assign match_score (0-100 integer):
        - 85-100: Exceeds/meets all criticals + most supporting, with equal or greater experience.
        - 70-84: Meets most criticals, minor gaps/1-2 year shortfall easily bridged.
        - 50-69: Foundational but significant gaps or experience shortfall requiring training.
        - 0-49: Missing multiple criticals or experience far too junior (apply caps strictly).
        7. Reasoning: 100 words max, evidence-based. Start with overall fit, highlight strengths with resume quotes, explain score (why capped or high), detail gaps.
        8. Missing skills: Only CRITICAL items from JD that are clearly absent/insufficient in resume (exact phrasing from JD). Max 5 items; ignore supporting/nice-to-haves.

        ### INPUT:

        [[CANDIDATE RESUME]]:
        {resume_text}
                
        [[JOB DESCRIPTION]]:
        {jd_text}


        ### OUTPUT FORMAT (JSON ONLY):
        {{
            "match_score": <int: Between 0 and 100>,
            "reasoning": "<string: Concise explanation. Focus on WHY they can or cannot do the job.>",
            "missing_skills": [<list of strings: Missing skills>]
        }}
        """

        try:
            # Inference using Ollama
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                format='json',
                options={
                    'temperature': 0.1,  
                    'num_ctx': 12288, 
                    'top_p' : 0.1  
                }
            )

            # Token Usage Monitoring
            input_tokens = response.get('prompt_eval_count', 0)
            output_tokens = response.get('eval_count', 0)
            print(f"📊 [Local Token Usage] In: {input_tokens} | Out: {output_tokens} | Total: {input_tokens + output_tokens}")

            content = response['message']['content']
            return json.loads(content)

        except Exception as e:
            self.logger.error(f"Local inference failed: {e}")
            return self._get_default_response()

    def trigger_local_evaluate(self, resume: str, jd: str) -> pd.Series:
        """
        Public wrapper to facilitate pandas DataFrame integration.
        
        Args:
            resume (str): Candidate resume string.
            jd (str): Job description string.

        Returns:
            pd.Series: Match Score, Reasoning, and Missing Skills for DataFrame assignment.
        """
        result = self._evaluate_match(resume, jd)
        return pd.Series([result['match_score'], result['reasoning'], result['missing_skills']])

    def process_job_data(self, filename: str, resume_path: str):
        """
        Orchestrates the local processing flow from CSV reading to result saving.

        Args:
            filename (str): The target CSV file located in the filtered file directory.
            resume_path (str): The file path to the candidate's PDF resume.
        """
        start_time = time.time()
        
        try:
            # Resource Loading
            resume_str = load_resume_pdf(resume_path, logger=self.logger)
            path = Path(FILTERED_FILE_PATH / filename)
            df = pd.read_csv(path)
            self.logger.info(f"Loaded {len(df)} records for local processing.")

            # Processing
            self.logger.info(f"Engaging LocalLLMMatcher with model: {self.model}")
            
            # Using the trigger method for pandas apply
            results = df['Job Description'].apply(lambda x: self.trigger_local_evaluate(resume_str, x))
            df[['Match Score', 'Reasoning', 'Missing Skills']] = results

            # Automated Flagging
            df['Recommend Apply'] = np.where(df['Match Score'] >= 80, True, False)

            # Reorder columns and Save
            cols = [
                'Job Title', 'Company', 'Posted Ago', 'Min Salary', 'Max Salary', 
                'Recommend Apply', 'Match Score', 'Reasoning', 'Missing Skills', 
                'URL', 'Posted Time', 'Salary', 'Reposted', 'Job Description'
            ]
            df = df[cols]
            df.to_csv(path, index=False)
            
            elapsed = time.time() - start_time
            self.logger.info(f"Local process finished in {elapsed:.2f} seconds. Results saved to: {path}")

        except Exception as e:
            self.logger.critical(f"Local processing crashed: {e}")

# ================= MAIN EXECUTION =================
if __name__ == "__main__":
    setup_logging()
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Instantiate the local matcher
    # You can specify "llama3.1" or "gemma3:12b" here
    matcher = LocalLLMMatcher(model_name="gemma3:12b")
    
    matcher.process_job_data(
        filename='20260127_Arron_Machine Learning_filtered.csv',
        resume_path='Arron Chen Resume 2025 Updated.pdf'
    )