import sys
import logging
import click


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)

logger = logging.getLogger(__name__)

def handle_error(message, exit_code=1):
    """Handle errors with logging and exit"""
    logger.error(message)
    click.secho(f"Error: {message}", err=True, fg="red", bold=True)
    sys.exit(exit_code)
