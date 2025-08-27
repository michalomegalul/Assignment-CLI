#!/bin/bash

echo "Generating protobuf files..."
python -m grpc_tools.protoc --python_out=cli --grpc_python_out=cli --proto_path=. ../protos/file_service.proto

echo "Protobuf files generated successfully!"
echo "You can now run: docker-compose up -d"