import ollama
import logging
import json
import numpy as np
from utils.logger import setup_logging
from typing import Dict, Any
from utils.file_path import FILTERED_FILE_PATH
from pathlib import Path
import pandas as pd
import time
from utils.LLM_ICL import icl_example
from utils.resume_to_string import load_resume_pdf

class ResumeMatcher:
    def __init__(self, model_name: str):
        """
        Initializes the ResumeMatcher with a specific LLM model.
        
        Args:
            model_name (str): The Ollama model tag to use.
        """
        self.model = model_name

    def match(self, resume_text: str, jd_text: str):
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
            # 3. Inference
            response = ollama.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                format='json',  # Forces structured output
                options={
                    'temperature': 0.1,  
                    'num_ctx': 12288, 
                    'top_p' : 0.1  
                }
            )

            # --- 新增：获取并打印 Token 用量 ---
            input_tokens = response.get('prompt_eval_count', 0)
            output_tokens = response.get('eval_count', 0)
            
            # 使用 print 实时显示 (因为 logger 可能会被过滤或不显示在控制台)
            print(f"📊 [Token Usage] In: {input_tokens} | Out: {output_tokens} | Total: {input_tokens + output_tokens}")
            # --------------------------------

            content = response['message']['content']

            print(content)
            
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
    start = time.time()
    setup_logging()
    logger = logging.getLogger(__name__)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    matcher = ResumeMatcher(model_name="gemma3:12b") # or llama3.1
    # Convert pdf to text
    resume = load_resume_pdf('Arron Chen Resume 2025 Updated.pdf', logger = logger)
    filename = '20260127_Arron_Machine Learning_filtered.csv'
    path = Path(FILTERED_FILE_PATH/filename)
    df = pd.read_csv(path) # 可能要改
    df[['Match Score', 'Reasoning', 'Missing Skills']] = df['Job Description'].apply(lambda x: pd.Series(matcher.match(resume,x)))
    df['Recommend Apply'] = np.where(df['Match Score'] >= 60, True, False)
    df = df[['Job Title', 'Company', 'Posted Ago', 'Min Salary', 'Max Salary', 'Recommend Apply', 'Match Score', 'Reasoning', 'Missing Skills', 'URL', 'Posted Time', 'Salary', 'Reposted', 'Job Description']]
    df.to_csv(path, index = False)
    end = time.time()  
    print(f"全部耗时: {end - start:.2f} 秒")