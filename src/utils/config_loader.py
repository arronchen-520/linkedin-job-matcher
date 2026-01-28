import sys
import yaml
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

def load_config(config_path: str | Path) -> dict:
    logger = logging.getLogger(__name__)
    """Loads configuration from a YAML file."""
    path = Path(config_path)
    if not path.exists():
        logger.critical(f"Config file not found: {path.resolve()}")
        raise ValueError(f"Config file not found: {path}")
        
    try:
        return yaml.safe_load(path.read_text(encoding='utf-8'))
    except yaml.YAMLError as e:
        logger.critical(f"Error parsing YAML file: {e}")
        raise ValueError(f"Error parsing YAML file: {e}")

def validate_config(config: dict) -> dict:
    """
    Strictly validates configuration structure.
    Returns the config dict if valid, raises ValueError otherwise.
    """
    logger = logging.getLogger(__name__)
    if 'resume' not in config: # Required
        msg = "Missing 'sresume' section in config file."
        logger.critical(msg)
        raise ValueError(msg)
    if 'search' not in config: # Required
        msg = "Missing 'search' section in config file."
        logger.critical(msg)
        raise ValueError(msg)
    if 'distance' not in config['search']: # Optional
        msg = "Missing 'distance' in config file. Dafulting to 10."
        logger.info(msg)
        config['search']['distance'] = 10
    if 'period' not in config['search']: # Optional
        msg = "Missing 'period' in config file. Dafulting to 'Past 24 hours'."
        logger.info(msg)
        config['search']['period'] = 'Past 24 hours'
    required_fields = ['keyword', 'city']
    for field in required_fields:
        if field not in config['search']:
            msg = f"Missing required field '{field}' inside 'search' section."
            logger.critical(msg)
            raise ValueError(msg)
        if not config['search'][field]:
            msg = f"Field '{field}' cannot be empty."
            logger.critical(msg)
            raise ValueError(msg)
    return config

def get_run_parameters(config_path: str | Path) -> dict:
    """
        Consolidates logic to determine parameters.
        Args:
            config_path: Can be a file path string, a Path object, or None (to use default).
    """
    logger = logging.getLogger(__name__)
    params = {}
    
    if config_path:
        logger.info(f"Loading configuration from: {config_path}")
        config_data = load_config(config_path)
    else:
        logger.info("No config file provided. Using default config.")
        default_config = Path("config") / "default_setting.yaml"
        config_data = load_config(default_config)       
    
    try:
        validate_config(config_data)
        params['user_name'] = config_data.get('user_name', 'User')
        params['resume'] = config_data['resume'] # Validated above
        params['search'] = config_data['search']
        params['max_page'] = config_data.get('max_page', 8)
        # Safely get options with defaults
        options = config_data.get('options', {})
        params['headless'] = options.get('headless', False)
        params['tracing'] = options.get('tracing', False)
        params['trace_path'] = options.get('trace_path', 'trace.zip')
        params['company_list'] = config_data.get('company_list', [])
        params['repost'] = config_data.get('repost', False)
        params['salary'] = config_data.get('salary', False)
        
    except ValueError as e:
        logger.critical(f"Invalid Configuration: {e}")
        raise ValueError(f"Invalid Configuration: {e}")
    
    return params