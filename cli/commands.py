import click
from datetime import datetime
from .db import DatabaseManager
from .errors import handle_error

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Domain Management CLI"""
    pass


@cli.command()
def status():
    """Show database status"""
    click.echo(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] Database Status")
    
    try:
        db = DatabaseManager()
        stats = db.get_stats()
        
        click.echo("Database connected")
        click.echo(f"  Domains: {stats['total_domains']} total, {stats['active_domains']} active")
        click.echo(f"  Flags: {stats['total_flags']} total")
        
    except Exception as e:
        handle_error(f"Database error: {e}")


@cli.command()
def active_domains():
    """List active domains (registered, not expired)"""
    try:
        db = DatabaseManager()
        domains = db.get_active_domains()
        
        if domains:
            click.echo(f"Active domains ({len(domains)}):")
            for domain in domains:
                click.echo(f"  {domain}")
        else:
            handle_error("No active domains found")
            
    except Exception as e:
        handle_error(f"Error: {e}")


@cli.command()
def flagged_domains():
    """List domains that had both EXPIRED and OUTZONE flags"""
    try:
        db = DatabaseManager()
        domains = db.get_flagged_domains()
        
        if domains:
            click.echo(f"Flagged domains ({len(domains)}):")
            for domain in domains:
                click.echo(f"  {domain}")
        else:
            handle_error("No flagged domains found")

    except Exception as e:
        handle_error(f"Error: {e}")


if __name__ == '__main__':
    cli()