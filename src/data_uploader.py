from supabase import create_client
import pandas as pd
from dotenv import load_dotenv
import os

import logging

def upload_table_to_supabase(df: pd.DataFrame, params: dict, destination: str):
    logger = logging.getLogger('JobFilter')
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_API_KEY')
    try:
        supabase = create_client(url, key)
        logger.info('Successfully connecting to Supabase table. ')
    except:
        logging.error('Error connecting to Supabase table. ')
    df.fillna('', inplace = True)
    keyword = params['search']['keyword']
    today = pd.Timestamp.now().strftime('%Y-%m-%d')
    df['User'] = params['user_name']
    df['Keyword'] = keyword
    df['Date'] = today
    output = df.to_dict('records')
    try:
        supabase.table(destination).upsert(output, on_conflict="URL").execute()
        logger.info('Successfully loading data to Supabase table. ')
    except:
        logging.error('Error loading data to Supabase table. ')