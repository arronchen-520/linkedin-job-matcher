from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
LOG_DIR = PROJECT_ROOT / "data" / "log"
DATA_DIR = PROJECT_ROOT / "data" 
JD_DIR = DATA_DIR / "job_posts"
OUTPUT_DIR = DATA_DIR / "output"
USER_DATA_DIR = PROJECT_ROOT / 'browser_user'
RESUME_DIR = PROJECT_ROOT / 'data' / 'resumes'
EXTENSION_DIR = PROJECT_ROOT / 'extension' / '2.19.6_0'