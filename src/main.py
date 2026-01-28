import sys
from pathlib import Path
from utils.logger import setup_logging
from utils.config_loader import get_run_parameters
from utils.file_path import CONFIG_DIR
from job_scraper import LinkedInScraper
from salary_parser import SalaryParser
from deepseek_jd_resume_matcher import DeepseekMatcher
import logging
from datetime import datetime

def CareerCopilot(config_name):
    # Set up logging
    setup_logging(logging.INFO)
    logger = logging.getLogger(__name__)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Load config
    params = get_run_parameters(CONFIG_DIR / config_name)

    # Linkedin Scrapper
    try:
        scraper = LinkedInScraper()
        df = scraper.run(params) # Filtered jobs
        scraper.close()
    except Exception as e:
        logger.error(f"Application crashed at Linkedin Scrapper: {e}")
        sys.exit(1)
    
    # Salary Parser
    try:
        parser = SalaryParser(model_name="llama3.1")
        parser.process_df(df)
    except Exception as e:
        logger.error(f"Application crashed at Salary Parser: {e}")
        sys.exit(1)

    # Resume-JD Matcher
    try:
        matcher = DeepseekMatcher()
        current_date = datetime.now().strftime("%Y%m%d") # For filename
        df = matcher.process_job_data(
            df = df,
            resume = params['resume'],
            filename = f"{current_date}_{params['user_name']}_{params['search']['keyword']}.csv"
        )
    except Exception as e:
        logger.error(f"Application crashed at Resume-JD Matcher: {e}")
        sys.exit(1)

    return df

if __name__ == '__main__':
    CareerCopilot(config_name="config_arron.yaml")