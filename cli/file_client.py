import click
import requests
import sys
import uuid as uuid_lib
from .errors import handle_error, logger

# Import gRPC client functions
try:
    from ..grpc.client import stat_grpc_impl, read_grpc_impl
    grpc_available = True
except ImportError:
    logger.warning("gRPC client not available")
    grpc_available = False


def validate_uuid(uuid_str):
    """Simple UUID validation"""
    try:
        uuid_lib.UUID(uuid_str)
        return True
    except ValueError:
        return False


def write_output(content, output_file):
    """Write content to file or stdout"""
    if output_file == '-':
        click.echo(content)
    else:
        try:
            with open(output_file, 'w') as f:
                f.write(content)
            logger.info(f"Output written to {output_file}")
        except Exception as e:
            handle_error(f"Error writing to file: {e}")


def stat_rest(uuid, base_url, output):
    """Get file metadata via REST API"""
    logger.info(f"REST stat request for UUID: {uuid}")
    
    if not validate_uuid(uuid):
        handle_error("Invalid UUID format")
    
    # Construct REST API URL
    if not base_url.endswith('/'):
        base_url += '/'
    url = f"{base_url}file/{uuid}/stat/"
    
    logger.info(f"Making REST request to: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Format output in human-readable manner
            output_text = f"""Name: {data['name']}
Size: {data['size']} bytes
MIME Type: {data['mimetype']}
Created: {data['create_datetime']}"""
            write_output(output_text, output)
            logger.info("REST stat request completed successfully")
        elif response.status_code == 404:
            handle_error("File not found")
        elif response.status_code == 400:
            handle_error("Invalid UUID format")
        else:
            handle_error(f"Server returned status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        handle_error(f"Cannot connect to REST server at {base_url}")
    except requests.exceptions.Timeout:
        handle_error("Request timeout")
    except Exception as e:
        handle_error(f"REST request failed: {e}")


def read_rest(uuid, base_url, output):
    """Read file content via REST API"""
    logger.info(f"REST read request for UUID: {uuid}")
    
    if not validate_uuid(uuid):
        handle_error("Invalid UUID format")
    
    # Construct REST API URL
    if not base_url.endswith('/'):
        base_url += '/'
    url = f"{base_url}file/{uuid}/read/"
    
    logger.info(f"Making REST request to: {url}")
    
    try:
        response = requests.get(url, timeout=30, stream=True)
        
        if response.status_code == 200:
            if output == '-':
                # Stream to stdout
                for chunk in response.iter_content(chunk_size=8192):
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.buffer.flush()
            else:
                # Stream to file
                with open(output, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            logger.info("REST read request completed successfully")
        elif response.status_code == 404:
            handle_error("File not found")
        elif response.status_code == 400:
            handle_error("Invalid UUID format")
        else:
            handle_error(f"Server returned status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        handle_error(f"Cannot connect to REST server at {base_url}")
    except requests.exceptions.Timeout:
        handle_error("Request timeout")
    except Exception as e:
        handle_error(f"REST request failed: {e}")


def stat_grpc(uuid, grpc_server, output):
    """Get file metadata via gRPC - delegates to grpc_client"""
    if not grpc_available:
        handle_error("gRPC support not available")
    
    stat_grpc_impl(uuid, grpc_server, output)


def read_grpc(uuid, grpc_server, output):
    """Read file content via gRPC - delegates to grpc_client"""
    if not grpc_available:
        handle_error("gRPC support not available")
    
    read_grpc_impl(uuid, grpc_server, output)


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
    
    logger.info(f"File client started - backend: {backend}, command: {command}, UUID: {uuid}")
    
    # Route to appropriate backend and command
    if backend == 'rest':
        if command == 'stat':
            stat_rest(uuid, base_url, output)
        elif command == 'read':
            read_rest(uuid, base_url, output)
    elif backend == 'grpc':
        if command == 'stat':
            stat_grpc(uuid, grpc_server, output)
        elif command == 'read':
            read_grpc(uuid, grpc_server, output)


if __name__ == '__main__':
    file_client()