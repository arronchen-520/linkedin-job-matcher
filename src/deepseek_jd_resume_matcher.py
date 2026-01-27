import json
import os
import time
import logging
import pandas as pd
import numpy as np
import tiktoken
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

# Assuming these utilities are part of your local project structure
from utils.file_path import FILTERED_FILE_PATH
from utils.logger import setup_logging
from utils.resume_to_string import load_resume_pdf

class DeepseekMatcher:
    """
    A specialized matching engine powered by DeepSeek-V3.
    Designed to be integrated into the CareerCopilot ecosystem for high-precision 
    resume-to-JD alignment analysis.

    """

    def __init__(self, api_key: str = None, base_url: str = "https://api.deepseek.com"):
        """
        Initializes the DeepSeek client and loads environment variables.

        Args:
            api_key (str): DeepSeek API key. Defaults to DEEPSEEK_API_KEY from .env.
            base_url (str): The target API endpoint.
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("API Key not found. Please set DEEPSEEK_API_KEY in .env")
        
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.logger = logging.getLogger(__name__)

    def _get_token_count(self, text: str, model_encoding: str = "gpt-4") -> int:
        """
        Calculates token count to manage context limits and optimize API costs.

        Args:
            text (str): Input text string.
            model_encoding (str): Encoding standard to utilize.

        Returns:
            int: Total token count estimate.
        """
        text = str(text)
        try:
            encoding = tiktoken.encoding_for_model(model_encoding)
            return len(encoding.encode(text))
        except Exception as e:
            self.logger.warning(f"Token counting failed: {e}, falling back to character-based estimation.")
            return len(text) // 4

    def _evaluate_match(self, resume_text: str, jd_text: str) -> dict:
        """
        Internal method to execute the DeepSeek API call for single JD evaluation.

        Args:
            resume_text (str): Cleaned resume text content.
            jd_text (str): Cleaned job description content.

        Returns:
            dict: Structured evaluation results containing score, reasoning, and gaps.
        """
        # 1. Token Safety Gate
        jd_token_count = self._get_token_count(jd_text)
        if jd_token_count > 10000:
            self.logger.warning(f"JD too long ({jd_token_count} tokens). Aborting API call.")
            return {
                "match_score": np.nan,
                "reasoning": "JOB DESCRIPTION TOO LONG: Exceeded 10,000 token limit. Manual review required.",
                "missing_skills": []
            }

        system_instruction = """
        You are an elite Technical Talent Acquisition Specialist with 20 years of experience. 
        Analyze the alignment between a candidate's resume and a job description. 

        ### SCORING RUBRIC:
        * 90-100: Perfect fit. Candidate meets ALL hard requirements and seniority levels.
        * 80-89: Strong Match. Only missing minor "nice-to-have" tools or has minor (within 25% safe zone) seniority gap.
        * 60-79: Moderate Match. Core skills match but missing specific domain or tools.
        * 0-59: Reject. Deal-breakers present (Language mismatch, huge seniority gap).

        ### CRITICAL RULES:
        * Be skeptical: Prioritize verifiable skills and evidence over self-claims.
        * Seniority Delta: If the candidate's years of experience is "significantly" lower than the job requirement, the score should be < 60.
        * Anti-assumption: Do not infer unstated expertise (e.g., no "Python → FastAPI"). 

        ### OUTPUT:
        Output strictly in JSON. No preamble. No markdown code blocks.
        Keys: 'match_score' (int), 'reasoning' (2-sentence string), 'missing_skills' (list of strings).
        """

        user_content = f"RESUME:\n{resume_text}\n\n\nJOB DESCRIPTION:\n{jd_text}"
        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                stream=False
            )

            elapsed_time = time.time() - start_time
            usage = response.usage

            self.logger.info(
                f"API Success | Time: {elapsed_time:.2f}s | "
                f"Tokens: {usage.total_tokens} (Cache Hit: {getattr(usage, 'prompt_cache_hit_tokens', 0)})"
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            self.logger.error(f"DeepSeek API Error: {str(e)}")
            return None

    def trigger_deepseek_evaluate(self, resume: str, jd: str) -> pd.Series:
        """
        Public entry point for row-by-row DataFrame evaluation.
        
        Args:
            resume (str): Candidate resume string.
            jd (str): Job description string.

        Returns:
            pd.Series: Match Score, Reasoning, and Missing Skills for DataFrame assignment.
        """
        result = self._evaluate_match(resume, jd)
        if result is None:
            return pd.Series([0, "API Error: Consult system logs.", []])
        return pd.Series([result['match_score'], result['reasoning'], result['missing_skills']])

    def process_job_data(self, filename: str, resume_path: str):
        """
        Orchestrates the end-to-end evaluation flow from CSV loading to result persistence.

        Args:
            filename (str): The target CSV file located in the filtered file directory.
            resume_path (str): The file path to the candidate's PDF resume.
        """
        try:
            # Resource Loading
            resume_str = load_resume_pdf(resume_path, logger=self.logger)
            path = Path(FILTERED_FILE_PATH / filename)
            df = pd.read_csv(path)
            self.logger.info(f"Loaded {len(df)} records for matching.")

            # Processing
            self.logger.info("Engaging DeepSeekMatcher engine...")
            
            # Use trigger_deepseek_evaluate for pandas apply
            results = df['Job Description'].apply(lambda x: self.trigger_deepseek_evaluate(resume_str, x))
            df[['Match Score', 'Reasoning', 'Missing Skills']] = results

            # Automated Flagging
            df['Recommend Apply'] = df['Match Score'] >= 80

            # Data Integrity & Formatting
            cols = [
                'Job Title', 'Company', 'Posted Ago', 'Min Salary', 'Max Salary',
                'Recommend Apply', 'Match Score', 'Reasoning', 'Missing Skills',
                'URL', 'Posted Time', 'Salary', 'Reposted', 'Job Description'
            ]
            df = df[cols]
            df.to_csv(path, index=False)
            self.logger.info(f"Analysis complete. Results persisted to: {path}")

        except Exception as e:
            self.logger.critical(f"Matching process aborted due to fatal error: {e}")

if __name__ == "__main__":
    # Configure logging for the execution environment
    setup_logging()
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Instance execution
    matcher = DeepseekMatcher()
    matcher.process_job_data(
        filename='20260127_Arron_Machine Learning_filtered.csv',
        resume_path='Arron Chen Resume 2025 Updated.pdf'
    )