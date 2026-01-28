import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from utils.file_path import OUTPUT_DIR



def filter_eligible_jobs(df: pd.DataFrame, params: dict):
    """
    Filters the raw job list based on user preferences and saves a secondary CSV.
    
    Filter Logic:
    1. Keep job if Company is in `params['company_list']` OR if the job has `Salary` info.
    2. Filter based on the `Reposted` status preference.
    
    Args:
        df: Dataframe of scraped jobs.
        params (dict): Configuration dictionary containing 'company_list', 'user_name', and 'repost'.
    """
    logger = logging.getLogger('JobFilter')
    company_list = params['company_list']
    user = params['user_name']

    if company_list == []:
        logger.info(f"No company list provided. ")
        if not params['salary']:
            logger.info(f"No salary boolean provided. ")
        else:
            logger.info(f"Filtering jobs with salaries... ")
            df = df[df['Salary'] != '']
    else:
        if not params['salary']:
            logger.info(f"No salary boolean provided. ")
            df = df[df['Company'].isin(company_list)]
        else:
            logger.info(f"Filtering jobs with either intested companies or presented salaries... ")
            df = df[(df['Salary'] != '') | (df['Company'].isin(company_list))]
    
    # if not params['salary']:
    #     self.logger.info(f"No salary boolean provided. ")
    # else:
    #     self.logger.info(f"Filtering jobs with salaries... ")
    #     df = df[df['Salary'] != '']

    if params['repost']:
        logger.info(f"No repost boolean provided. ")
    else:
        logger.info(f"Filtering newly posted jobs... ")
        df = df[~df['Reposted']]

    current_date = datetime.now().strftime("%Y%m%d")
    search = params['search']
    filepath = Path(OUTPUT_DIR / f"{current_date}_{user}_{search['keyword']}.csv")
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    logger.info(f"Filtered {len(df)} eligible jobs and saved to {filepath}")
    return df