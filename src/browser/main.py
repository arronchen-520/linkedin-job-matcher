import os
import sys
import yaml
import logging
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from scraper import LinkedInScraper

# --- Constants & Configuration ---
BASE_DIR = Path(__file__).parent.parent.parent
LOG_DIR = BASE_DIR / "log"
DATA_DIR = BASE_DIR / "data" / "job_posts"
CONFIG_DIR = BASE_DIR / "config"

# --- Setup ---
# Make sure the folders exist
load_dotenv()
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"scraper_run_{current_time}.log"

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MainController")

def load_config(config_path: str) -> dict:
    """Loads configuration from a YAML file."""
    path = Path(config_path)
    if not path.exists():
        logger.critical(f"Config file not found: {path}")
        sys.exit(1)
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.critical(f"Error parsing YAML file: {e}")
        sys.exit(1)

def validate_config(config: dict) -> dict:
    """
    Strictly validates configuration structure.
    Returns the config dict if valid, raises ValueError otherwise.
    """
    if 'user_name' not in config:
        raise ValueError("Missing 'user_name' in config file.")
    if 'search' not in config:
        raise ValueError("Missing 'search' section in config file.")

    required_fields = ['keyword', 'city', 'distance', 'period']
    for field in required_fields:
        if field not in config['search']:
            raise ValueError(f"Missing required field '{field}' inside 'search' section.")
        if not config['search'][field]:
            raise ValueError(f"Field '{field}' cannot be empty.")

    return config

def get_run_parameters(args) -> dict:
    """
    Consolidates logic to determine parameters from CLI or Config file.
    Returns a normalized dictionary of settings.
    """
    params = {}
    
    if args.config:
        logger.info(f"Loading configuration from: {args.config}")
        config_data = load_config(args.config)
        try:
            validate_config(config_data)
            params['user_name'] = config_data['user_name']
            params['search'] = config_data['search']
            # Safely get options with defaults
            options = config_data.get('options', {})
            params['headless'] = options.get('headless', False)
        except ValueError as e:
            logger.critical(f"Invalid Configuration: {e}")
            sys.exit(1)
    else:
        logger.info("No config file provided. Using CLI arguments.")
        params['user_name'] = "CLI_User"
        params['search'] = {
            'keyword': args.keyword,
            'city': args.city,
            'distance': args.distance,
            'period': args.period
        }
        params['headless'] = args.headless
    
    return params

def run_scraping_task(params: dict, credentials: dict):
    """
    Encapsulates the core business logic: driving the scraper.
    """
    # Unpack parameters for clarity
    user = params['user_name']
    search = params['search']
    
    # Generate Filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    safe_keyword = search['keyword'].replace(" ", "_")
    filename = f"jobs_{user}_{safe_keyword}_{timestamp}.csv"
    full_path = DATA_DIR / filename

    logger.info(f"Starting task for [{user}]: {search['keyword']} in {search['city']}")

    bot = LinkedInScraper()
    try:
        bot.start(headless=params['headless'])
        bot.sign_in(credentials['email'], credentials['password'])
        
        bot.search_jobs(search['keyword'], search['city'])
        bot.filter_period(search['period'])
        bot.set_distance(search['distance'])
        bot.scrape_available_jobs()
        bot.save_to_csv(str(full_path))
        
        logger.info("Task completed successfully.")
        
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user.")
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
    finally:
        bot.close()

def main():
    parser = argparse.ArgumentParser(description="LinkedIn Job Scraper CLI")
    parser.add_argument("--config", type=str, help="Path to YAML config file")
    parser.add_argument("--keyword", type=str, default="Machine Learning")
    parser.add_argument("--city", type=str, default="Toronto, Ontario, Canada")
    parser.add_argument("--distance", type=int, default=10)
    parser.add_argument("--period", type=str, default="Past 24 hours")
    parser.add_argument("--headless", action="store_true")
    
    args = parser.parse_args()

    # 1. Check Credentials First (Fail Fast)
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    if not email or not password:
        logger.critical("Missing credentials in .env file.")
        sys.exit(1)

    # 2. Resolve Parameters
    params = get_run_parameters(args)

    # 3. Execute Business Logic
    run_scraping_task(params, {'email': email, 'password': password})

if __name__ == "__main__":
    main()