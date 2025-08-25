import click
import requests
import sys
import uuid as uuid_lib
from .logger import log_api_request, get_structured_logger, log_cli_command, create_audit_log_entry


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
@log_cli_command("file_client")
def file_client(backend, grpc_server, base_url, output, command, uuid):
    """File client for REST/gRPC operations
    
    Commands:
      stat    Prints the file metadata in a human-readable manner.
      read    Outputs the file content.
    """
    logger = get_structured_logger("cli.file_client")
    
    logger.info("File client operation started", extra={
        'extra_fields': {
            'backend': backend,
            'command': command,
            'uuid': uuid,
            'output': output,
            'base_url': base_url if backend == 'rest' else None,
            'grpc_server': grpc_server if backend == 'grpc' else None
        }
    })
    
    # Validate UUID
    if not validate_uuid(uuid):
        logger.error("Invalid UUID format provided", extra={
            'extra_fields': {
                'provided_uuid': uuid
            }
        })
        click.echo("Error: Invalid UUID format", err=True)
        sys.exit(1)
    
    logger.debug("UUID validation passed")
    
    try:
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
                
        # Create audit log entry for successful operations
        create_audit_log_entry(
            action=f"file_{command}",
            resource=f"file:{uuid}",
            backend=backend,
            output_location=output
        )
        
    except Exception as e:
        logger.error("File client operation failed", extra={
            'extra_fields': {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'backend': backend,
                'command': command
            }
        }, exc_info=True)
        raise


@log_api_request("file_service_rest")
def stat_rest(uuid, base_url, output):
    """Get file metadata via REST API"""
    logger = get_structured_logger("api.file_stat")
    
    try:
        url = f"{base_url.rstrip('/')}/file/{uuid}/stat/"
        logger.debug("Making REST API request for file metadata", extra={
            'extra_fields': {
                'url': url,
                'uuid': uuid,
                'operation': 'stat'
            }
        })
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 404:
            logger.warning("File not found", extra={
                'extra_fields': {
                    'uuid': uuid,
                    'status_code': response.status_code
                }
            })
            click.echo("File not found", err=True)
            sys.exit(1)
        
        response.raise_for_status()
        data = response.json()
        
        logger.info("File metadata retrieved successfully", extra={
            'extra_fields': {
                'uuid': uuid,
                'file_name': data.get('name'),
                'file_size': data.get('size'),
                'mime_type': data.get('mimetype'),
                'status_code': response.status_code,
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
        })
        
        # Format as human-readable text
        output_text = f"""Name: {data.get('name', 'Unknown')}
Size: {data.get('size', 0)} bytes
MIME Type: {data.get('mimetype', 'Unknown')}
Created: {data.get('create_datetime', 'Unknown')}"""
        
        write_output(output_text, output)
        
    except requests.RequestException as e:
        logger.error("REST API request failed", extra={
            'extra_fields': {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'url': url,
                'uuid': uuid
            }
        }, exc_info=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@log_api_request("file_service_rest")
def read_rest(uuid, base_url, output):
    """Read file content via REST API"""
    logger = get_structured_logger("api.file_read")
    
    try:
        url = f"{base_url.rstrip('/')}/file/{uuid}/read/"
        logger.debug("Making REST API request for file content", extra={
            'extra_fields': {
                'url': url,
                'uuid': uuid,
                'operation': 'read',
                'output_destination': output
            }
        })
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 404:
            logger.warning("File not found", extra={
                'extra_fields': {
                    'uuid': uuid,
                    'status_code': response.status_code
                }
            })
            click.echo("File not found", err=True)
            sys.exit(1)
        
        response.raise_for_status()
        
        content_length = len(response.content) if response.content else 0
        logger.info("File content retrieved successfully", extra={
            'extra_fields': {
                'uuid': uuid,
                'content_length': content_length,
                'content_type': response.headers.get('content-type'),
                'status_code': response.status_code,
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'output_to_file': output != '-'
            }
        })
        
        if output == '-':
            # Output to stdout as text
            click.echo(response.text)
        else:
            # Save to file as binary to preserve exact content
            with open(output, 'wb') as f:
                f.write(response.content)
            logger.info("File content saved to disk", extra={
                'extra_fields': {
                    'output_file': output,
                    'bytes_written': len(response.content)
                }
            })
        
    except requests.RequestException as e:
        logger.error("REST API request failed", extra={
            'extra_fields': {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'url': url,
                'uuid': uuid
            }
        }, exc_info=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def stat_grpc(uuid, grpc_server, output):
    """Get file metadata via gRPC (not implemented)"""
    logger = get_structured_logger("api.grpc_stat")
    logger.warning("gRPC backend not implemented", extra={
        'extra_fields': {
            'uuid': uuid,
            'grpc_server': grpc_server,
            'operation': 'stat'
        }
    })
    click.echo("Error: gRPC backend not implemented", err=True)
    sys.exit(1)


def read_grpc(uuid, grpc_server, output):
    """Read file content via gRPC (not implemented)"""
    logger = get_structured_logger("api.grpc_read")
    logger.warning("gRPC backend not implemented", extra={
        'extra_fields': {
            'uuid': uuid,
            'grpc_server': grpc_server,
            'operation': 'read'
        }
    })
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