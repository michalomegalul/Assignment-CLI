import sys
import logging
import os


def setup_logging():
    """Setup logging based on environment variables"""
    log_level = os.getenv('LOG_LEVEL', 'info').upper()
    app_env = os.getenv('APP_ENV', 'production').lower()
    
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    if app_env == 'development' and log_level == 'DEBUG':
        logging.basicConfig(
            level=level_map.get(log_level, logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    elif app_env == 'development':
        logging.basicConfig(
            level=level_map.get(log_level, logging.INFO),
            format="%(levelname)s: %(message)s"
        )
    else:
        logging.basicConfig(
            level=logging.ERROR,
            format="%(levelname)s: %(message)s"
        )
    
    return logging.getLogger(__name__)

logger = setup_logging()

def handle_error(message, exit_code=1):
    """Handle errors with logging and exit"""
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(exit_code)