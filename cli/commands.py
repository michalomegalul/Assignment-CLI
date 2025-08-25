import click
from datetime import datetime
from .database import DatabaseManager
from .file_client import file_client
from .logging_config import setup_logging
from .logger import log_cli_command, get_structured_logger, create_audit_log_entry


@click.group()
@click.version_option(version='1.0.0')
@click.pass_context
def cli(ctx):
    """Domain Management CLI by michal"""
    # Initialize logging system on CLI startup only if not in help mode
    if ctx.invoked_subcommand is not None:
        setup_logging()
        logger = get_structured_logger("cli.main")
        logger.info("Domain Management CLI started", extra={
            'extra_fields': {
                'version': '1.0.0',
                'author': 'michal',
                'command': ctx.invoked_subcommand
            }
        })


@cli.command()
@log_cli_command("status")
def status():
    """Show database status"""
    logger = get_structured_logger("cli.status")
    
    try:
        logger.info("Retrieving database status")
        click.echo(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] Database Status")
        click.echo("Author: michal")
        
        db = DatabaseManager()
        stats = db.get_stats()
        
        logger.info("Database connection successful", extra={
            'extra_fields': {
                'total_domains': stats['total_domains'],
                'active_domains': stats['active_domains'],
                'total_flags': stats['total_flags']
            }
        })
        
        click.echo("Database connected")
        click.echo(f"  Domains: {stats['total_domains']} total, {stats['active_domains']} active")
        click.echo(f"  Flags: {stats['total_flags']} total")
        
        # Create audit log entry
        create_audit_log_entry(
            action="database_status_check",
            resource="database",
            result_domains=stats['total_domains'],
            result_flags=stats['total_flags']
        )
        
    except Exception as e:
        logger.error("Database connection failed", extra={
            'extra_fields': {
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
        }, exc_info=True)
        click.echo(f"✗ Database error: {e}")
        raise


@cli.command()
@log_cli_command("active_domains")
def active_domains():
    """List active domains (registered, not expired)"""
    logger = get_structured_logger("cli.active_domains")
    
    try:
        logger.info("Fetching active domains")
        db = DatabaseManager()
        domains = db.get_active_domains()
        
        if domains:
            logger.info("Active domains retrieved successfully", extra={
                'extra_fields': {
                    'domain_count': len(domains),
                    'first_domain': domains[0] if domains else None
                }
            })
            click.echo(f"Active domains ({len(domains)}):")
            for domain in domains:
                click.echo(f"  {domain}")
        else:
            logger.info("No active domains found")
            click.echo("No active domains found")
            
        # Create audit log entry
        create_audit_log_entry(
            action="list_active_domains",
            resource="domains",
            result_count=len(domains)
        )
            
    except Exception as e:
        logger.error("Failed to retrieve active domains", extra={
            'extra_fields': {
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
        }, exc_info=True)
        click.echo(f"Error: {e}")
        raise


@cli.command()
@log_cli_command("flagged_domains")
def flagged_domains():
    """List domains that had both EXPIRED and OUTZONE flags"""
    logger = get_structured_logger("cli.flagged_domains")
    
    try:
        logger.info("Fetching flagged domains")
        db = DatabaseManager()
        domains = db.get_flagged_domains()
        
        if domains:
            logger.info("Flagged domains retrieved successfully", extra={
                'extra_fields': {
                    'domain_count': len(domains),
                    'first_domain': domains[0] if domains else None
                }
            })
            click.echo(f"Flagged domains ({len(domains)}):")
            for domain in domains:
                click.echo(f"  {domain}")
        else:
            logger.info("No flagged domains found")
            click.echo("No flagged domains found")
            
        # Create audit log entry
        create_audit_log_entry(
            action="list_flagged_domains",
            resource="domains",
            result_count=len(domains)
        )
            
    except Exception as e:
        logger.error("Failed to retrieve flagged domains", extra={
            'extra_fields': {
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
        }, exc_info=True)
        click.echo(f"Error: {e}")
        raise


# Add file-client command
cli.add_command(file_client, name='file-client')


if __name__ == '__main__':
    cli()