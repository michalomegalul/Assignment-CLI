import sys
import logging
import click

logger = logging.getLogger(__name__)

def handle_error(message, exit_code=1):
    """Handle errors with logging and exit"""
    logger.error(message)
    click.echo(f"Error: {message}", err=True)
    sys.exit(exit_code)