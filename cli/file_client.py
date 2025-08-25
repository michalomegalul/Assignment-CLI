import click
import requests
import sys
import time
import uuid as uuid_lib
from .logging_config import get_logger, log_api_request, set_correlation_id


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
    logger = get_logger(__name__)
    correlation_id = set_correlation_id()
    
    logger.info(f"File client command started", extra={
        'correlation_id': correlation_id,
        'backend': backend,
        'command': command,
        'uuid': uuid,
        'base_url': base_url if backend == 'rest' else None,
        'grpc_server': grpc_server if backend == 'grpc' else None,
        'output': output
    })
    
    # Validate UUID
    if not validate_uuid(uuid):
        logger.error(f"Invalid UUID format provided: {uuid}", extra={'correlation_id': correlation_id})
        click.echo("Error: Invalid UUID format", err=True)
        sys.exit(1)
    
    try:
        if backend == 'rest':
            if command == 'stat':
                stat_rest(uuid, base_url, output, correlation_id)
            else:  # read
                read_rest(uuid, base_url, output, correlation_id)
        else:  # grpc
            if command == 'stat':
                stat_grpc(uuid, grpc_server, output, correlation_id)
            else:  # read
                read_grpc(uuid, grpc_server, output, correlation_id)
                
        logger.info(f"File client command completed successfully", extra={
            'correlation_id': correlation_id,
            'backend': backend,
            'command': command
        })
        
    except Exception as e:
        logger.error(f"File client command failed: {e}", extra={
            'correlation_id': correlation_id,
            'backend': backend,
            'command': command,
            'error_type': type(e).__name__
        }, exc_info=True)
        raise


def stat_rest(uuid, base_url, output, correlation_id):
    """Get file metadata via REST API"""
    logger = get_logger(__name__)
    start_time = time.time()
    
    try:
        url = f"{base_url.rstrip('/')}/file/{uuid}/stat/"
        
        logger.debug(f"Making REST API call for file stat", extra={
            'correlation_id': correlation_id,
            'url': url,
            'uuid': uuid
        })
        
        response = requests.get(url, timeout=30)
        duration_ms = (time.time() - start_time) * 1000
        
        log_api_request(
            logger, 
            "GET", 
            url, 
            response.status_code, 
            duration_ms,
            operation="stat",
            uuid=uuid,
            correlation_id=correlation_id
        )
        
        if response.status_code == 404:
            logger.warning(f"File not found", extra={
                'correlation_id': correlation_id,
                'uuid': uuid,
                'status_code': 404
            })
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
        
        logger.info(f"File stat retrieved successfully", extra={
            'correlation_id': correlation_id,
            'uuid': uuid,
            'file_name': data.get('name', 'Unknown'),
            'file_size': data.get('size', 0),
            'mime_type': data.get('mimetype', 'Unknown')
        })
        
    except requests.RequestException as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"REST API request failed for file stat: {e}", extra={
            'correlation_id': correlation_id,
            'uuid': uuid,
            'url': url,
            'duration_ms': f"{duration_ms:.2f}",
            'error_type': type(e).__name__
        })
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def read_rest(uuid, base_url, output, correlation_id):
    """Read file content via REST API"""
    logger = get_logger(__name__)
    start_time = time.time()
    
    try:
        url = f"{base_url.rstrip('/')}/file/{uuid}/read/"
        
        logger.debug(f"Making REST API call for file read", extra={
            'correlation_id': correlation_id,
            'url': url,
            'uuid': uuid
        })
        
        response = requests.get(url, timeout=30)
        duration_ms = (time.time() - start_time) * 1000
        
        log_api_request(
            logger, 
            "GET", 
            url, 
            response.status_code, 
            duration_ms,
            operation="read",
            uuid=uuid,
            correlation_id=correlation_id
        )
        
        if response.status_code == 404:
            logger.warning(f"File not found", extra={
                'correlation_id': correlation_id,
                'uuid': uuid,
                'status_code': 404
            })
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
        
        logger.info(f"File content retrieved successfully", extra={
            'correlation_id': correlation_id,
            'uuid': uuid,
            'content_length': len(response.content),
            'output_file': output if output != '-' else 'stdout'
        })
        
    except requests.RequestException as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"REST API request failed for file read: {e}", extra={
            'correlation_id': correlation_id,
            'uuid': uuid,
            'url': url,
            'duration_ms': f"{duration_ms:.2f}",
            'error_type': type(e).__name__
        })
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def stat_grpc(uuid, grpc_server, output, correlation_id):
    """Get file metadata via gRPC (not implemented)"""
    logger = get_logger(__name__)
    logger.warning(f"gRPC backend not implemented for stat operation", extra={
        'correlation_id': correlation_id,
        'uuid': uuid,
        'grpc_server': grpc_server
    })
    click.echo("Error: gRPC backend not implemented", err=True)
    sys.exit(1)


def read_grpc(uuid, grpc_server, output, correlation_id):
    """Read file content via gRPC (not implemented)"""
    logger = get_logger(__name__)
    logger.warning(f"gRPC backend not implemented for read operation", extra={
        'correlation_id': correlation_id,
        'uuid': uuid,
        'grpc_server': grpc_server
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