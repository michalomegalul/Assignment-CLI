import sys
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)

def handle_error(message, exit_code=1):
    """Handle errors with logging and exit"""
    logger.error(message)
    sys.exit(exit_code)
