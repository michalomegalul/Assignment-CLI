import uuid as uuid_lib
import requests
import sys
import click
from .errors import handle_error

def validate_uuid(uuid_str):
    """Validate if string is a valid UUID format"""
    if uuid_str is None or uuid_str == '':
        return False
    
    try:
        uuid_lib.UUID(uuid_str)
        return True
    except (ValueError, TypeError):
        return False

def write_output(content, output_file):
    """Write content to output file or stdout"""
    if output_file == '-':
        click.echo(content)
    else:
        with open(output_file, 'w') as f:
            f.write(content)

def stat_rest(uuid_str, base_url, output):
    """Get file statistics via REST API"""
    if not base_url.endswith('/'):
        base_url += '/'

    url = f"{base_url}file/{uuid_str}/stat/"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()

        output_lines = [
            f"Name: {data.get('name', 'Unknown')}",
            f"Size: {data.get('size', 0)} bytes",
            f"MIME Type: {data.get('mimetype', 'Unknown')}",
            f"Created: {data.get('create_datetime', 'Unknown')}"
        ]

        content = '\n'.join(output_lines)
        write_output(content, output)

    except requests.exceptions.RequestException as e:
        handle_error(str(e))
    except Exception as e:
        handle_error(str(e))

def read_rest(uuid_str, base_url, output):
    """Read file content via REST API"""
    if not validate_uuid(uuid_str):
        handle_error("Invalid UUID format")

    if not base_url.endswith('/'):
        base_url += '/'
    
    url = f"{base_url}file/{uuid_str}/read/"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        if output == '-':
            sys.stdout.buffer.write(response.content)
        else:
            with open(output, 'wb') as f:
                f.write(response.content)
                
    except requests.exceptions.RequestException as e:
        handle_error(f"Error: {e}")
    except Exception as e:
        handle_error(f"Error: {e}")

def stat_grpc(uuid, grpc_server, output):
    """Get file metadata via gRPC - imports from separate client module"""
    from .grpc_client import stat_grpc_impl
    stat_grpc_impl(uuid, grpc_server, output)

def read_grpc(uuid, grpc_server, output):
    """Read file content via gRPC - imports from separate client module"""
    from .grpc_client import read_grpc_impl
    read_grpc_impl(uuid, grpc_server, output)

@click.command()
@click.option('--backend', type=click.Choice(['rest', 'grpc']), default='grpc',
              help='Set a backend to be used, choices are grpc and rest. Default is grpc.')
@click.option('--grpc-server', default='localhost:50051',
              help='Set a host and port of the gRPC server. Default is localhost:50051.')
@click.option('--base-url', default='http://web:5000/',
              help='Set a base URL for a REST server. Default is http://web:5000/.')
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
        handle_error("Invalid UUID format")

    if backend == 'rest':
        if command == 'stat':
            stat_rest(uuid, base_url, output)
        else:
            read_rest(uuid, base_url, output)
    else:  # grpc
        if command == 'stat':
            stat_grpc(uuid, grpc_server, output)
        else:
            read_grpc(uuid, grpc_server, output)

if __name__ == '__main__':
    file_client()