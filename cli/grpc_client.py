import grpc
import uuid as uuid_lib
from datetime import datetime
from typing import Optional, Iterator
import os
import sys

"""Imports generated gRPC code"""
try:
    import cli.generated.file_service_pb2 as file_service_pb2
    import cli.generated.file_service_pb2_grpc as file_service_pb2_grpc
except ImportError:
    pass


class GrpcClient:
    """gRPC client for file operations"""
    
    def __init__(self, server_address: str = "localhost:50051"):
        self.server_address = server_address
        self.channel = None
        self.stub = None
    
    