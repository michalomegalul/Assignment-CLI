import click
import requests
import sys
import uuid as uuid_lib
from .errors import handle_error, logger
import os


def validate_uuid(uuid_str):
    """Simple UUID validation with better error handling"""
    if uuid_str is None or not isinstance(uuid_str, str):
        return False
    
    try:
        uuid_lib.UUID(uuid_str)
        return True
    except (ValueError, TypeError):
        return False


def write_output(content, output_file):
    """Write content to file or stdout"""
    if output_file == '-':
        click.echo(content)
    else:
        try:
            with open(output_file, 'w') as f:
                f.write(content)
            logger.debug(f"Output written to {output_file}")
        except Exception as e:
            handle_error(f"Error writing to file: {e}")


def stat_rest(uuid, base_url, output):
    """Get file metadata via REST API with better error handling"""
    logger.debug(f"REST stat request for UUID: {uuid}")
    
    if not validate_uuid(uuid):
        handle_error("Invalid UUID format")
    
    # Construct REST API URL
    if not base_url.endswith('/'):
        base_url += '/'
    url = f"{base_url}file/{uuid}/stat/"
    
    logger.debug(f"Making REST request to: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle missing fields gracefully
            name = data.get('name', 'Unknown')
            size = data.get('size', 0)
            mimetype = data.get('mimetype', 'application/octet-stream')
            created = data.get('create_datetime', 'Unknown')
            
            output_text = f"""Name: {name}
Size: {size} bytes
MIME Type: {mimetype}
Created: {created}"""
            write_output(output_text, output)
            logger.debug("REST stat request completed successfully")
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
    logger.debug(f"REST read request for UUID: {uuid}")
    
    if not validate_uuid(uuid):
        handle_error("Invalid UUID format")
    
    if not base_url.endswith('/'):
        base_url += '/'
    url = f"{base_url}file/{uuid}/read/"
    
    logger.debug(f"Making REST request to: {url}")
    
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
            logger.debug("REST read request completed successfully")
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


@click.group(invoke_without_command=True)
@click.option('--backend', type=click.Choice(['rest']), default='rest',
              help='Set a backend to be used, only rest is supported. Default is rest.')
@click.option('--base-url', default='http://web:5000/',
              help='Set a base URL for a REST server. Default is http://web:5000/.')
@click.option('--output', default='-',
              help='Set the file where to store the output. Default is -, i.e. the stdout.')
@click.pass_context
def file_client(ctx, backend, base_url, output):
    """File client CLI application for retrieving data from REST backend.
    
    Author: michalomegalul
    Date: 2025-08-27 14:52:50 UTC
    Assignment: CLI File Client Implementation
    """
    ctx.ensure_object(dict)
    ctx.obj['backend'] = backend
    ctx.obj['base_url'] = base_url
    ctx.obj['output'] = output


@file_client.command()
@click.argument('uuid')
@click.pass_context
def stat(ctx, uuid):
    """Prints the file metadata in a human-readable manner."""
    backend = ctx.obj['backend']
    base_url = ctx.obj['base_url']
    output = ctx.obj['output']
    
    logger.info(f"File client started - backend: {backend}, command: stat, UUID: {uuid}")
    
    if backend == 'rest':
        stat_rest(uuid, base_url, output)


@file_client.command()
@click.argument('uuid')
@click.pass_context
def read(ctx, uuid):
    """Outputs the file content."""
    backend = ctx.obj['backend']
    base_url = ctx.obj['base_url']
    output = ctx.obj['output']
    
    logger.info(f"File client started - backend: {backend}, command: read, UUID: {uuid}")
    
    if backend == 'rest':
        read_rest(uuid, base_url, output)


if __name__ == '__main__':
    file_client()