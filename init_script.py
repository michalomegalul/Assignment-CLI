import os
import uuid
import json
import requests
import psycopg2
from datetime import datetime, timedelta
import click
from dotenv import load_dotenv

load_dotenv()


class DataInitializer:
    """Initialize test data for the application"""
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/domains')
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
    
    def create_test_files(self):
        """Create test files for different formats"""
        test_files = {}
        
        # JSON test file
        json_data = {
            "domains": [
                {
                    "fqdn": "json-example.com",
                    "registered_at": "2025-08-24 13:29:27+00",
                    "unregistered_at": None
                },
                {
                    "fqdn": "expired_example.org",
                    "registered_at": "2023-01-01 00:00:00+00",
                    "unregistered_at": "2024-01-01 00:00:00+00"
                },
                {
                    "fqdn": "active-example.net",
                    "registered_at": "2024-06-01 00:00:00+00",
                    "unregistered_at": None
                }
            ],
            "flags": [
                {
                    "domain_fqdn": "expired_example.org",
                    "flag": "EXPIRED",
                    "valid_from": "2024-01-01 00:00:00+00",
                    "valid_to": None
                },
                {
                    "domain_fqdn": "expired_example.org",
                    "flag": "OUTZONE",
                    "valid_from": "2024-06-01 00:00:00+00",
                    "valid_to": "2024-08-01 00:00:00+00"
                },
                {
                    "domain_fqdn": "active-example.net",
                    "flag": "EXPIRED",
                    "valid_from": "2024-12-01 00:00:00+00",
                    "valid_to": "2024-12-15 00:00:00+00"
                }
            ]
        }
        test_files['test.json'] = json.dumps(json_data, indent=2)
        
        # CSV test file
        csv_data = """fqdn,registered_at,unregistered_at
csv-example.com,2025-08-24 13:29:27+00,
csv-expired.org,2023-01-01 00:00:00+00,2024-01-01 00:00:00+00
csv-active.net,2024-06-01 00:00:00+00,
csv-another.info,2022-01-01 00:00:00+00,"""
        test_files['test.csv'] = csv_data
        
        # Text test file
        text_data = """# Domain list for testing
text-example.com
text-expired.org
text-active.net
text-another.info"""
        test_files['test.txt'] = text_data
        
        return test_files
    
    def populate_database_directly(self):
        """Populate database with test data directly"""
        click.echo("Populating database with test data...")
        
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    # Clear existing test data 
                    cur.execute("DELETE FROM domain_flag WHERE domain_id IN (SELECT id FROM domain WHERE fqdn LIKE '%test%')")
                    cur.execute("DELETE FROM domain WHERE fqdn LIKE '%test%'")
                    
                    # Insert test domains
                    test_domains = [
                        ('direct-test.com', '2025-08-24 13:29:27+00', None),
                        ('direct-expired.org', '2023-01-01 00:00:00+00', '2024-01-01 00:00:00+00'),
                        ('direct-active.net', '2024-06-01 00:00:00+00', None),
                        ('direct-flagged.info', '2022-01-01 00:00:00+00', None),
                    ]
                    
                    domain_ids = {}
                    for fqdn, reg_at, unreg_at in test_domains:
                        cur.execute("""
                            INSERT INTO domain (fqdn, registered_at, unregistered_at)
                            VALUES (%s, %s, %s)
                            RETURNING id
                        """, (fqdn, reg_at, unreg_at))
                        domain_ids[fqdn] = cur.fetchone()[0]
                        click.echo(f"  ✓ Added domain: {fqdn}")
                    
                    # Insert test flags
                    test_flags = [
                        ('direct-expired.org', 'EXPIRED', '2024-01-01 00:00:00+00', None),
                        ('direct-flagged.info', 'EXPIRED', '2024-01-01 00:00:00+00', None),
                        ('direct-flagged.info', 'OUTZONE', '2024-06-01 00:00:00+00', None),
                    ]
                    
                    for fqdn, flag, valid_from, valid_to in test_flags:
                        if fqdn in domain_ids:
                            cur.execute("""
                                INSERT INTO domain_flag (domain_id, flag, valid_from, valid_to)
                                VALUES (%s, %s, %s, %s)
                            """, (domain_ids[fqdn], flag, valid_from, valid_to))
                            click.echo(f"  ✓ Added flag: {flag} for {fqdn}")
                    
                    conn.commit()
                    click.echo(click.style("Database populated successfully!", fg='magenta'))

        except Exception as e:
            click.echo(click.style(f"Database population failed: {e}", err=True, fg='red'))

    def create_test_file_directory(self):
        """Create test files directory"""
        test_dir = "test_files"
        os.makedirs(test_dir, exist_ok=True)
        
        files = self.create_test_files()
        file_info = {}
        
        for filename, content in files.items():
            filepath = os.path.join(test_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
            
            # Generate UUID for each file
            file_uuid = str(uuid.uuid4())
            file_info[file_uuid] = {
                'filename': filename,
                'filepath': filepath,
                'size': len(content.encode('utf-8')),
                'mimetype': self._get_mimetype(filename)
            }
            
            click.echo(f"✓ Created {filename} -> UUID: {file_uuid}")
        
        # Save file mapping for testing
        with open(os.path.join(test_dir, 'file_mapping.json'), 'w') as f:
            json.dump(file_info, f, indent=2)
        
        click.echo(f"Test files created in {test_dir}/")
        return file_info
    
    def _get_mimetype(self, filename):
        """Get MIME type for filename"""
        if filename.endswith('.json'):
            return 'application/json'
        elif filename.endswith('.csv'):
            return 'text/csv'
        elif filename.endswith('.txt'):
            return 'text/plain'
        else:
            return 'application/octet-stream'
    
    def show_test_commands(self, file_info):
        """Show example commands for testing"""
        click.echo("\nReady to test! Try these commands:")
        click.echo("\n# Check status")
        click.echo("docker-compose exec app python cli.py status")
        
        click.echo("\n# Query existing domains")
        click.echo("docker-compose exec app python cli.py query-active-domains")
        click.echo("docker-compose exec app python cli.py query-flagged-domains")
        
        if file_info:
            click.echo("\n# Test with generated UUIDs (when you have API server):")
            for file_uuid, info in list(file_info.items())[:2]:  # Show first 2
                click.echo(f"docker-compose exec app python cli.py fetch-domains --uuid {file_uuid} --api-type rest")
        
        click.echo("\n# Run tests")
        click.echo("docker-compose exec app python -m pytest tests/ -v")


@click.command()
@click.option('--database-only', is_flag=True, help='Only populate database, skip file creation')
@click.option('--files-only', is_flag=True, help='Only create test files, skip database')
def main(database_only, files_only):
    """Initialize test data for Domain Management CLI"""
    click.echo("Domain Management CLI - Data Initializer")
    click.echo("=" * 50)
    
    initializer = DataInitializer()
    file_info = {}
    
    if not files_only:
        initializer.populate_database_directly()
    
    if not database_only:
        file_info = initializer.create_test_file_directory()
    
    initializer.show_test_commands(file_info)


if __name__ == '__main__':
    main()