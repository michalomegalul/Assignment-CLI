import click
from datetime import datetime
from .database import DatabaseManager
from .file_client import file_client
from .logging_config import setup_logging, get_logger, set_correlation_id
import os


@click.group()
@click.version_option(version='1.0.0')
@click.pass_context
def cli(ctx):
    """Domain Management CLI by michal"""
    # Initialize logging on first run
    if not hasattr(cli, '_logging_initialized'):
        # Setup logging based on environment variables
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_to_file = os.getenv('LOG_TO_FILE', 'true').lower() == 'true'
        log_to_console = os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true'
        log_dir = os.getenv('LOG_DIR', 'logs')
        
        setup_logging(
            log_level=log_level,
            log_to_file=log_to_file,
            log_to_console=log_to_console,
            log_dir=log_dir
        )
        
        logger = get_logger(__name__)
        logger.info("Domain Management CLI starting", extra={
            'version': '1.0.0',
            'author': 'michal',
            'log_level': log_level,
            'log_to_file': log_to_file,
            'log_to_console': log_to_console
        })
        
        cli._logging_initialized = True


@cli.command()
def status():
    """Show database status"""
    logger = get_logger(__name__)
    correlation_id = set_correlation_id()
    
    logger.info("Status command started", extra={'correlation_id': correlation_id})
    
    click.echo(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] Database Status")
    click.echo("Author: michal")
    
    try:
        db = DatabaseManager()
        stats = db.get_stats()
        
        click.echo("Database connected")
        click.echo(f"  Domains: {stats['total_domains']} total, {stats['active_domains']} active")
        click.echo(f"  Flags: {stats['total_flags']} total")
        
        logger.info("Status command completed successfully", extra={
            'correlation_id': correlation_id,
            'total_domains': stats['total_domains'],
            'active_domains': stats['active_domains'],
            'total_flags': stats['total_flags']
        })
        
    except Exception as e:
        click.echo(f"✗ Database error: {e}")
        logger.error(f"Status command failed: {e}", extra={
            'correlation_id': correlation_id,
            'error_type': type(e).__name__
        }, exc_info=True)


@cli.command()
def active_domains():
    """List active domains (registered, not expired)"""
    logger = get_logger(__name__)
    correlation_id = set_correlation_id()
    
    logger.info("Active domains command started", extra={'correlation_id': correlation_id})
    
    try:
        db = DatabaseManager()
        domains = db.get_active_domains()
        
        if domains:
            click.echo(f"Active domains ({len(domains)}):")
            for domain in domains:
                click.echo(f"  {domain}")
        else:
            click.echo("No active domains found")
            
        logger.info("Active domains command completed successfully", extra={
            'correlation_id': correlation_id,
            'domain_count': len(domains)
        })
            
    except Exception as e:
        click.echo(f"Error: {e}")
        logger.error(f"Active domains command failed: {e}", extra={
            'correlation_id': correlation_id,
            'error_type': type(e).__name__
        }, exc_info=True)


@cli.command()
def flagged_domains():
    """List domains that had both EXPIRED and OUTZONE flags"""
    logger = get_logger(__name__)
    correlation_id = set_correlation_id()
    
    logger.info("Flagged domains command started", extra={'correlation_id': correlation_id})
    
    try:
        db = DatabaseManager()
        domains = db.get_flagged_domains()
        
        if domains:
            click.echo(f"Flagged domains ({len(domains)}):")
            for domain in domains:
                click.echo(f"  {domain}")
        else:
            click.echo("No flagged domains found")
            
        logger.info("Flagged domains command completed successfully", extra={
            'correlation_id': correlation_id,
            'domain_count': len(domains)
        })
            
    except Exception as e:
        click.echo(f"Error: {e}")
        logger.error(f"Flagged domains command failed: {e}", extra={
            'correlation_id': correlation_id,
            'error_type': type(e).__name__
        }, exc_info=True)


# Add file-client command
cli.add_command(file_client, name='file-client')


if __name__ == '__main__':
    cli()