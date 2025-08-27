import grpc
from concurrent import futures
import os
import json
import uuid as uuid_lib
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp
from cli.errors import handle_error, logger

try:
    from protos import file_service_pb2 as file_pb2
    from protos import file_service_pb2_grpc as file_pb2_grpc

except ImportError:
    handle_error("gRPC protobuf files not found. Run: python generate_proto.py")

class FileService(file_pb2_grpc.FileServicer):
    """gRPC File Service Implementation
    
    This class implements the File service defined in file.proto.
    Each method corresponds to an RPC method in the proto file.
    """
    
    def __init__(self):
        self.upload_folder = os.getenv("UPLOAD_FOLDER", "/app/files")
        self.metadata_file = os.getenv("METADATA_FILE", "/app/metadata.json")
        os.makedirs(self.upload_folder, exist_ok=True)
        logger.info(f"FileService initialized - upload_folder: {self.upload_folder}")
    
    def load_metadata(self):
        """Load file metadata from JSON file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                return {}
        return {}
    
    def stat(self, request, context):
        """RPC method: Get file metadata
        
        gRPC Flow:
        1. Client sends StatRequest with UUID
        2. Server validates UUID and looks up metadata  
        3. Server returns StatReply with file info OR sets error status
        4. Client receives response or gRPC exception
        """
        logger.info(f"stat() called for UUID: {request.uuid.value}")
        
        try:
            # Validate UUID format
            uuid_str = request.uuid.value
            uuid_lib.UUID(uuid_str)
        except ValueError:
            logger.error(f"Invalid UUID format: {uuid_str}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID format")
            return file_pb2.StatReply()
        
        try:
            metadata_store = self.load_metadata()
            
            if uuid_str not in metadata_store:
                logger.error(f"File not found: {uuid_str}")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("File not found")
                return file_pb2.StatReply()
            
            file_info = metadata_store[uuid_str]
            logger.info(f"Found file: {file_info['name']}")
            
            # Convert datetime string to protobuf Timestamp
            create_time = Timestamp()
            try:
                dt = datetime.fromisoformat(file_info['create_datetime'].replace('Z', '+00:00'))
                create_time.FromDatetime(dt)
            except Exception as e:
                logger.error(f"Error parsing datetime: {e}")
                # Fallback to current time
                create_time.FromDatetime(datetime.utcnow())
            
            # Create protobuf response
            data = file_pb2.StatReply.Data(
                create_datetime=create_time,
                size=file_info['size'],
                mimetype=file_info['mimetype'],
                name=file_info['name']
            )
            
            logger.info("stat() completed successfully")
            return file_pb2.StatReply(data=data)
            
        except Exception as e:
            logger.error(f"Database error in stat(): {e}")
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("Database error")
            return file_pb2.StatReply()
    
    def read(self, request, context):
        """RPC method: Read file content (streaming)
        
        gRPC Streaming Flow:
        1. Client sends ReadRequest with UUID and chunk size
        2. Server validates UUID and opens file
        3. Server yields multiple ReadReply messages (streaming)
        4. Client receives each chunk as it's sent
        5. Stream ends when file is fully sent or error occurs
        """
        logger.info(f"read() called for UUID: {request.uuid.value}")
        
        try:
            # Validate UUID format
            uuid_str = request.uuid.value
            uuid_lib.UUID(uuid_str)
        except ValueError:
            logger.error(f"Invalid UUID format: {uuid_str}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid UUID format")
            return
        
        try:
            metadata_store = self.load_metadata()
            
            if uuid_str not in metadata_store:
                logger.error(f"File not found: {uuid_str}")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("File not found")
                return
            
            file_info = metadata_store[uuid_str]
            file_path = file_info['file_path']
            
            if not os.path.exists(file_path):
                logger.error(f"File missing on disk: {file_path}")
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("File missing on disk")
                return
            
            # Determine chunk size (default 8KB for streaming)
            chunk_size = int(request.size) if request.size > 0 else 8192
            logger.info(f"Streaming file {file_info['name']} in {chunk_size} byte chunks")
            
            # Stream file content
            total_bytes = 0
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    # Create protobuf response with chunk
                    data = file_pb2.ReadReply.Data(data=chunk)
                    yield file_pb2.ReadReply(data=data)
                    total_bytes += len(chunk)
            
            logger.info(f"read() completed successfully ({total_bytes} bytes streamed)")
                    
        except Exception as e:
            logger.error(f"File system error in read(): {e}")
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("File system error")
            return

def serve():
    """Start the gRPC server
    
    Server Lifecycle:
    1. Create ThreadPoolExecutor for handling concurrent requests
    2. Add our FileService to the server
    3. Bind to network port (default 50051)
    4. Start accepting connections
    5. Wait for shutdown signal
    """
    port = os.getenv("GRPC_PORT", "50051")
    
    try:
        # Create server with thread pool (max 10 concurrent requests)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        
        # Register our service implementation
        file_pb2_grpc.add_FileServicer_to_server(FileService(), server)
        
        # Bind to all interfaces on specified port
        listen_addr = f'[::]:{port}'
        server.add_insecure_port(listen_addr)
        
        logger.info(f"Starting gRPC server on {listen_addr}")
        server.start()
        
        try:
            # Keep server running until interrupted
            server.wait_for_termination()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            server.stop(grace_period=5)
            
    except Exception as e:
        handle_error(f"Failed to start gRPC server: {e}")

if __name__ == '__main__':
    serve()