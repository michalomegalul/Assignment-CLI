#!/bin/bash
echo "Setting up demo files for File Client CLI..."

mkdir -p /app/files


echo "Hello, this is a sample text file for testing the File Client CLI!" > /app/files/sample.txt
echo '{"message": "This is a test JSON file", "timestamp": "2025-08-27T14:25:31Z", "purpose": "CLI testing", "author": "michalomegalul"}' > /app/files/test.json
echo "Binary content example - this could be any file type. Created for testing purposes by michalomegalul on 2025-08-27." > /app/files/document.bin

SAMPLE_SIZE=$(wc -c < /app/files/sample.txt)
JSON_SIZE=$(wc -c < /app/files/test.json)
BIN_SIZE=$(wc -c < /app/files/document.bin)

{
  "12345678-1234-5678-9abc-123456789abc": {
    "name": "sample.txt",
    "size": ${SAMPLE_SIZE},
    "mimetype": "text/plain",
    "create_datetime": "2025-08-27T14:25:31Z",
    "file_path": "/app/files/sample.txt"
  },
  "87654321-4321-8765-cba9-987654321098": {
    "name": "test.json",
    "size": ${JSON_SIZE},
    "mimetype": "application/json",
    "create_datetime": "2025-08-27T14:25:31Z",
    "file_path": "/app/files/test.json"
  },
  "11111111-2222-3333-4444-555555555555": {
    "name": "document.bin",
    "size": ${BIN_SIZE},
    "mimetype": "application/octet-stream",
    "create_datetime": "2025-08-27T14:25:31Z",
    "file_path": "/app/files/document.bin"
  }
}
EOF

echo "Demo files created successfully in /app/files/"
echo "Files created:"
echo "- /app/files/sample.txt (${SAMPLE_SIZE} bytes)"
echo "- /app/files/test.json (${JSON_SIZE} bytes)"  
echo "- /app/files/document.bin (${BIN_SIZE} bytes)"
echo "- /app/files/metadata.json (metadata store)"
echo ""
echo "Available test UUIDs:"
echo "- 12345678-1234-5678-9abc-123456789abc (sample.txt)"
echo "- 87654321-4321-8765-cba9-987654321098 (test.json)"
echo "- 11111111-2222-3333-4444-555555555555 (document.bin)"
echo ""
echo "Test commands:"
echo "  file-client stat 12345678-1234-5678-9abc-123456789abc"
echo "  file-client read 87654321-4321-8765-cba9-987654321098"
echo ""
echo "Upload helper available at: files/upload_file.py"
echo "Starting File Server..."