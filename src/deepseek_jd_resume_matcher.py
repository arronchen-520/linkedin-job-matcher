import json
import os
import time
import logging
import pandas as pd
import numpy as np
import tiktoken
import tqdm
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
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
        """
        load_dotenv()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            self.logger.critical("DEEPSEEK_API_KEY not found in environment or .env file.")
            raise ValueError("API Key not found. Please set DEEPSEEK_API_KEY in .env")
        
        self.client = OpenAI(api_key=self.api_key, base_url=base_url)
        self.logger.info(f"DeepseekMatcher initialized with base_url: {base_url}")

    def _get_token_count(self, text: str, model_encoding: str = "gpt-4") -> int:
        """
        Calculates token count to manage context limits and optimize API costs.
        """
        text = str(text)
        try:
            encoding = tiktoken.encoding_for_model(model_encoding)
            count = len(encoding.encode(text))
            self.logger.debug(f"Token count calculated: {count} tokens.")
            return count
        except Exception as e:
            self.logger.warning(f"Tiktoken failed: {e}. Falling back to character-based heuristic.")
            return len(text) // 4

    def _evaluate_match(self, resume_text: str, jd_text: str, job_type: str) -> dict:
        """
        Internal method to execute the DeepSeek API call for single JD evaluation.
        """
        # 1. Token Safety Gate
        jd_token_count = self._get_token_count(jd_text)
        resume_token_count = self._get_token_count(resume_text)
        
        if jd_token_count > 10000:
            self.logger.error(f"Safety Gate: JD is too large ({jd_token_count} tokens). Skipping API call to prevent cost overflow.")
            return {
                "match_score": np.nan,
                "reasoning": "JOB DESCRIPTION TOO LONG: Exceeded 10,000 token limit. Manual review required.",
                "missing_skills": []
            }

        system_instruction = """
        You are an elite Technical Talent Acquisition Specialist with 20 years of experience. 
        Analyze the alignment between a candidate's resume and a job description. 

        ### SCORING RUBRIC:
        * 80-100: Strong Match. High likelihood of being accepted by hiring manager. Only missing minor "nice-to-have" tools or has minor (within 20% safe zone) seniority gap.
        * 60-79: Moderate Match. Likelihood depends on candidate's interview prep. Core skills match but missing specific domain or tools.
        * 0-59: Reject. Deal-breakers present (Language mismatch, huge seniority gap).

        ### CRITICAL RULES:
        * Be skeptical: Prioritize verifiable skills and evidence over self-claims.
        * Seniority Delta: If the candidate's years of experience is "significantly" lower than the job requirement, the score should be < 60.
        * Anti-assumption: Do not infer unstated expertise (e.g., no "Python → FastAPI"). 
        * Overqualified: If the candidate is clearly overqualified, the score should be < 70.

        ### OUTPUT:
        Output strictly in JSON. No preamble. No markdown code blocks.
        Keys: 'match_score' (int), 'reasoning' (2-sentence string), 'missing_skills' (list of strings).
        """

        user_content = f"RESUME:\n{resume_text}\n\n Note: The candidate is interested in {job_type} jobs. \n\nJOB DESCRIPTION:\n{jd_text}"
        self.logger.debug(f"Sending payload to DeepSeek. JD length: {len(jd_text)} chars.")
        
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

            self.logger.debug(
                f"DeepSeek Match Complete | Time: {elapsed_time:.2f}s | "
                f"Total Tokens: {usage.total_tokens} | "
                f"Prompt Cache Hit: {getattr(usage, 'prompt_cache_hit_tokens', 0)}"
            )

            return json.loads(response.choices[0].message.content)

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse DeepSeek JSON response: {e}")
            return None
        except Exception as e:
            self.logger.error(f"DeepSeek API call failed: {str(e)}", exc_info=True)
            return None

    def trigger_deepseek_evaluate(self, resume: str, jd: str, job_type: str) -> pd.Series:
        """
        Public entry point for row-by-row DataFrame evaluation.
        """
        self.logger.debug("Triggering evaluation for single row...")
        result = self._evaluate_match(resume, jd, job_type)
        
        if result is None:
            self.logger.warning("Evaluation returned None. Defaulting to error Series.")
            return pd.Series([0, "API Error: Consult system logs.", []])
            
        return pd.Series([result['match_score'], result['reasoning'], result['missing_skills']])

    def process_job_data(self, df: pd.DataFrame, resume: str, job_type = 'full time', filename = 'result.csv'):
        """
        Orchestrates the end-to-end evaluation flow from CSV loading to result persistence.
        """
        self.logger.info(f"Starting batch process: {len(df)} jobs total.")
        try:
            # Resource Loading
            resume_str = load_resume_pdf(resume, logger=self.logger)
            self.logger.info(f"Successfully loaded and parsed resume: {resume}")
            
            path = Path(FILTERED_FILE_PATH / filename)
            self.logger.info(f"Final results will be saved to: {path}")

            # Processing
            self.logger.info("Iterating through jobs via DeepSeekMatcher...")
            tqdm.pandas(desc="DeepSeek Matching Progress")

            # Use trigger_deepseek_evaluate for pandas apply
            # Note: For large DFs, consider a progress bar or batching
            results = df['Job Description'].progress_apply(lambda x: self.trigger_deepseek_evaluate(resume_str, x, job_type))
            
            self.logger.info("Applying AI results to DataFrame columns...")
            df[['Match Score', 'Reasoning', 'Missing Skills']] = results

            # Automated Flagging
            high_match_count = (df['Match Score'] >= 80).sum()
            df['Recommend Apply'] = df['Match Score'] >= 80
            self.logger.info(f"Filtering complete. Found {high_match_count} high-score matches.")

            # Data Integrity & Formatting
            cols = [
                'Job Title', 'Company', 'Posted Ago', 'Min Salary', 'Max Salary',
                'Recommend Apply', 'Match Score', 'Reasoning', 'Missing Skills',
                'URL', 'Posted Time', 'Salary', 'Reposted', 'Job Description'
            ]
            df = df[cols]
            
            # File Persistence
            df.to_csv(path, index=False)
            self.logger.info(f"Job processing successful. File exported: {path}")
            
            return df
            
        except FileNotFoundError as e:
            self.logger.error(f"File system error: {e}")
        except Exception as e:
            self.logger.critical(f"Matching process aborted due to fatal error: {e}", exc_info=True)
            return None

# if __name__ == "__main__":
#     # Configure logging for the execution environment
#     setup_logging()
#     logging.getLogger("httpx").setLevel(logging.WARNING)

#     # Instance execution
#     matcher = DeepseekMatcher()
#     matcher.process_job_data(
#         filename='20260127_Arron_Machine Learning_filtered.csv',
#         resume_path='Arron Chen Resume 2025 Updated.pdf'
#     )