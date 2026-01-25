from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
LOG_DIR = PROJECT_ROOT / "data" / "log"
DATA_DIR = PROJECT_ROOT / "data" / 'job_posts'
COMPLETE_FILE_PATH = DATA_DIR / "complete_posts"
FILTERED_FILE_PATH = DATA_DIR / "filtered_posts"
USER_DATA_DIR = PROJECT_ROOT / 'browser_user'