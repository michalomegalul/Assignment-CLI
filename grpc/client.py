import grpc
import sys
from ..cli.errors import handle_error, logger
from ..cli.file_client import validate_uuid, write_output

# Import the generated protobuf files
try:
    import file_pb2
    import file_pb2_grpc
except ImportError:
    handle_error("gRPC protobuf files not found. Run: python generate_proto.py")

def create_grpc_channel(grpc_server):
    """Create a gRPC channel with proper error handling"""
    try:
        logger.info(f"Connecting to gRPC server: {grpc_server}")
        channel = grpc.insecure_channel(grpc_server)
        
        # Test the connection with a timeout
        grpc.channel_ready_future(channel).result(timeout=5)
        logger.info("gRPC connection established")
        return channel
        
    except grpc.FutureTimeoutError:
        handle_error(f"Failed to connect to gRPC server {grpc_server}: Connection timeout")
    except Exception as e:
        handle_error(f"Failed to connect to gRPC server {grpc_server}: {e}")

def stat_grpc_impl(uuid_str, grpc_server, output):
    """Get file metadata via gRPC
    
    How it works:
    1. Validate UUID locally first (fail fast)
    2. Create gRPC channel to server
    3. Create protobuf request message
    4. Call server's stat() method
    5. Handle gRPC status codes and convert to user-friendly errors
    6. Format response same as REST API
    """
    if not validate_uuid(uuid_str):
        handle_error("Invalid UUID format")
    
    logger.info(f"Getting file stats for UUID: {uuid_str}")
    
    try:
        # Step 1: Create gRPC connection
        channel = create_grpc_channel(grpc_server)
        stub = file_pb2_grpc.FileStub(channel)
        
        # Step 2: Create protobuf request
        uuid_msg = file_pb2.Uuid(value=uuid_str)
        request = file_pb2.StatRequest(uuid=uuid_msg)
        
        # Step 3: Make the gRPC call with timeout
        logger.info("Calling gRPC stat method")
        response = stub.stat(request, timeout=30)
        
        # Step 4: Process response (convert protobuf timestamp to string)
        create_time = response.data.create_datetime.ToDatetime().isoformat() + 'Z'
        
        output_lines = [
            f"Name: {response.data.name}",
            f"Size: {response.data.size} bytes", 
            f"MIME Type: {response.data.mimetype}",
            f"Created: {create_time}"
        ]
        
        content = '\n'.join(output_lines)
        write_output(content, output)
        
        logger.info("File stats retrieved successfully")
        channel.close()
        
    except grpc.RpcError as e:
        # gRPC specific error handling - map gRPC status codes to user messages
        if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
            handle_error("Invalid UUID format")
        elif e.code() == grpc.StatusCode.NOT_FOUND:
            handle_error("File not found")
        elif e.code() == grpc.StatusCode.FAILED_PRECONDITION:
            handle_error("Database error on server")
        elif e.code() == grpc.StatusCode.UNAVAILABLE:
            handle_error(f"gRPC server {grpc_server} is unavailable")
        elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
            handle_error("Request timeout - server took too long to respond")
        else:
            handle_error(f"gRPC error: {e.details()}")
    except Exception as e:
        handle_error(f"Unexpected error: {e}")

def read_grpc_impl(uuid_str, grpc_server, output):
    """Read file content via gRPC streaming
    
    How streaming works:
    1. Client sends one ReadRequest
    2. Server responds with multiple ReadReply messages (chunks)
    3. Client processes each chunk as it arrives
    4. Connection closes when server is done sending
    """
    if not validate_uuid(uuid_str):
        handle_error("Invalid UUID format")
    
    logger.info(f"Reading file content for UUID: {uuid_str}")
    
    try:
        # Step 1: Create gRPC connection 
        channel = create_grpc_channel(grpc_server)
        stub = file_pb2_grpc.FileStub(channel)
        
        # Step 2: Create protobuf request (size=0 means whole file)
        uuid_msg = file_pb2.Uuid(value=uuid_str)
        request = file_pb2.ReadRequest(uuid=uuid_msg, size=0)
        
        # Step 3: Make streaming gRPC call
        logger.info("Calling gRPC read method (streaming)")
        response_stream = stub.read(request, timeout=60)
        
        # Step 4: Process streaming response
        total_bytes = 0
        if output == '-':
            # Stream to stdout
            for response in response_stream:
                chunk = response.data.data
                sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()
                total_bytes += len(chunk)
        else:
            # Stream to file
            with open(output, 'wb') as f:
                for response in response_stream:
                    chunk = response.data.data
                    f.write(chunk)
                    total_bytes += len(chunk)
        
        logger.info(f"File read successfully ({total_bytes} bytes)")
        channel.close()
        
    except grpc.RpcError as e:
        # Same error mapping as stat
        if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
            handle_error("Invalid UUID format")
        elif e.code() == grpc.StatusCode.NOT_FOUND:
            handle_error("File not found") 
        elif e.code() == grpc.StatusCode.FAILED_PRECONDITION:
            handle_error("Database or filesystem error on server")
        elif e.code() == grpc.StatusCode.UNAVAILABLE:
            handle_error(f"gRPC server {grpc_server} is unavailable")
        elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
            handle_error("Request timeout - file too large or server too slow")
        else:
            handle_error(f"gRPC error: {e.details()}")
    except Exception as e:
        handle_error(f"Unexpected error: {e}")