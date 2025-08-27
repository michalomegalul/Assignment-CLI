#!/bin/bash

echo "Generating protobuf files..."

PROTO_DIR="grpc/protos"
OUT_DIR="grpc/protos"

if [ -d "$PROTO_DIR" ]; then
    python -m grpc_tools.protoc \
        --python_out=$OUT_DIR \
        --grpc_python_out=$OUT_DIR \
        --proto_path=$PROTO_DIR \
        $PROTO_DIR/file_service.proto
    chown $(whoami):$(whoami) $OUT_DIR/file_service_pb2*.py 2>/dev/null || true
    echo "Protobuf files generated successfully!"
else
    echo "Error: Cannot find $PROTO_DIR directory"
    exit 1
fi

echo "You can now run: docker-compose up -d"
