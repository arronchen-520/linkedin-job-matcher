from supabase import create_client
import pandas as pd
from dotenv import load_dotenv
import os
import logging

def upload_table_to_supabase(df: pd.DataFrame):
    logger = logging.getLogger('JobFilter')
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_API_KEY')
    try:
        supabase = create_client(url, key)
        logger.info('Successfully connecting to Supabase table. ')
    except:
        logging.error('Error connecting to Supabase table. ')
    df.fillna('', inplace = True)
    output = df.to_dict('records')
    try:
        supabase.table("JOB_DETAILS_COMPLETE").upsert(output, on_conflict="URL").execute()
        logger.info('Successfully loading data to Supabase table. ')
    except:
        logging.error('Error loading data to Supabase table. ')