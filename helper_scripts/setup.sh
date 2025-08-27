#!/bin/bash
echo "Generating protobuf files..."

if [ -d "protos" ]; then
    python -m grpc_tools.protoc --python_out=protos/ --grpc_python_out=protos/ --proto_path=protos protos/file_service.proto
    chown $(whoami):$(whoami) protos/file_service_pb2*.py 2>/dev/null || true
    echo "Protobuf files generated successfully!"
else
    echo "Error: Cannot find protos directory"
    exit 1
fi
