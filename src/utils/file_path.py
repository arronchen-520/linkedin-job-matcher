from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
LOG_DIR = PROJECT_ROOT / "data" / "log"
DATA_DIR = PROJECT_ROOT / "data"
COMPLETE_FILE_PATH = PROJECT_ROOT / "data" / "complete_posts"
FILTERED_FILE_PATH = PROJECT_ROOT / "data" / "filtered_posts"
USER_DATA_DIR = PROJECT_ROOT / 'browser_user'