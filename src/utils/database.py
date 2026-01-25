import sqlite3
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

class JobDatabase:
    def __init__(self, db_path: str = "data/jobs.db"):
        """
        Initializes the database connection and ensures the table exists.
        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self._init_table()

    def _init_table(self):
        """
        Creates the 'jobs' table if it does not already exist.
        Schema includes fields for job details, status tracking, and timestamps.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 'id' is the Primary Key. 'status' defaults to 'NEW' for future processing.
        c.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                location TEXT,
                url TEXT,
                description TEXT,
                salary TEXT,
                status TEXT DEFAULT 'NEW',
                match_score INTEGER,
                match_reason TEXT,
                created_at DATETIME,
                updated_at DATETIME
            )
        ''')
        conn.commit()
        conn.close()

    def generate_id(self, url: str) -> Optional[str]:
        """
        Generates a unique MD5 hash based on the job URL.
        This ensures duplicate URLs result in the same ID.
        """
        if not url:
            return None
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def save_jobs(self, job_list: List[Dict]) -> int:
        """
        Saves a list of job dictionaries to the database.
        Uses INSERT OR IGNORE to handle duplicates efficiently.
        
        Args:
            job_list (List[Dict]): List of job data dictionaries.
            
        Returns:
            int: The number of new jobs successfully inserted.
        """
        if not job_list:
            return 0
            
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        new_count = 0
        
        for job in job_list:
            # Generate unique ID from URL (fallback to existing ID if present)
            job_id = self.generate_id(job.get('url')) or job.get('id')
            
            # Prepare data tuple for insertion
            data = (
                job_id,
                job.get('title'),
                job.get('company'),
                job.get('location'),
                job.get('url'),
                job.get('description'),
                job.get('salary'),
                datetime.now(),
                datetime.now()
            )

            try:
                # INSERT OR IGNORE skips the row if the Primary Key (id) already exists
                c.execute('''
                    INSERT OR IGNORE INTO jobs 
                    (id, title, company, location, url, description, salary, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', data)
                
                # c.rowcount returns 1 if a row was added, 0 if ignored
                if c.rowcount > 0:
                    new_count += 1
                    
            except sqlite3.Error as e:
                print(f"[DB Error] Failed to save job '{job.get('title')}': {e}")

        conn.commit()
        conn.close()
        return new_count