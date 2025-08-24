import click
import requests
import sys
import uuid as uuid_lib


def validate_uuid(uuid_str):
    """Simple UUID validation"""
    try:
        uuid_lib.UUID(uuid_str)
        return True
    except ValueError:
        return False


@click.command()
@click.option('--backend', type=click.Choice(['rest', 'grpc']), default='grpc',
              help='Set a backend to be used, choices are grpc and rest. Default is grpc.')
@click.option('--grpc-server', default='localhost:50051',
              help='Set a host and port of the gRPC server. Default is localhost:50051.')
@click.option('--base-url', default='http://localhost/',
              help='Set a base URL for a REST server. Default is http://localhost/.')
@click.option('--output', default='-',
              help='Set the file where to store the output. Default is -, i.e. the stdout.')
@click.argument('command', type=click.Choice(['stat', 'read']))
@click.argument('uuid')
def file_client(backend, grpc_server, base_url, output, command, uuid):
    """File client for REST/gRPC operations
    
    Commands:
      stat    Prints the file metadata in a human-readable manner.
      read    Outputs the file content.
    """
    
    # Validate UUID
    if not validate_uuid(uuid):
        click.echo("Error: Invalid UUID format", err=True)
        sys.exit(1)
    
    if backend == 'rest':
        if command == 'stat':
            stat_rest(uuid, base_url, output)
        else:  # read
            read_rest(uuid, base_url, output)
    else:  # grpc
        if command == 'stat':
            stat_grpc(uuid, grpc_server, output)
        else:  # read
            read_grpc(uuid, grpc_server, output)


def stat_rest(uuid, base_url, output):
    """Get file metadata via REST API"""
    try:
        url = f"{base_url.rstrip('/')}/file/{uuid}/stat/"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 404:
            click.echo("File not found", err=True)
            sys.exit(1)
        
        response.raise_for_status()
        data = response.json()
        
        # Format as human-readable text
        output_text = f"""Name: {data.get('name', 'Unknown')}
Size: {data.get('size', 0)} bytes
MIME Type: {data.get('mimetype', 'Unknown')}
Created: {data.get('create_datetime', 'Unknown')}"""
        
        write_output(output_text, output)
        
    except requests.RequestException as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def read_rest(uuid, base_url, output):
    """Read file content via REST API"""
    try:
        url = f"{base_url.rstrip('/')}/file/{uuid}/read/"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 404:
            click.echo("File not found", err=True)
            sys.exit(1)
        
        response.raise_for_status()
        
        if output == '-':
            # Output to stdout as text
            click.echo(response.text)
        else:
            # Save to file as binary to preserve exact content
            with open(output, 'wb') as f:
                f.write(response.content)
        
    except requests.RequestException as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def stat_grpc(uuid, grpc_server, output):
    """Get file metadata via gRPC (not implemented)"""
    click.echo("Error: gRPC backend not implemented", err=True)
    sys.exit(1)


def read_grpc(uuid, grpc_server, output):
    """Read file content via gRPC (not implemented)"""
    click.echo("Error: gRPC backend not implemented", err=True)
    sys.exit(1)


def write_output(content, output_file):
    """Write content to file or stdout"""
    if output_file == '-':
        click.echo(content)
    else:
        with open(output_file, 'w') as f:
            f.write(content)


if __name__ == '__main__':
    file_client()