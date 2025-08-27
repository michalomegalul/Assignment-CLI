#!/bin/bash
set -euo pipefail

echo "====================================="
echo "         Test Runner"
echo "====================================="

echo "[1/1] Running tests..."
echo "Running all pytest tests..."
docker-compose exec -T app python -m pytest tests/ -v --tb=short || {
  echo "Tests failed!"
  exit 1
}

echo ""
echo "====================================="
echo "    Integration Testing CLI"
echo "====================================="

echo ""
echo "1. Testing file-client help command:"
echo "$ file-client --help"
docker-compose exec -T app file-client --help

echo ""
echo "2. Testing file-client with demo UUIDs:"
echo "$ file-client stat 12345678-1234-5678-9abc-123456789abc"
docker-compose exec -T app file-client stat 12345678-1234-5678-9abc-123456789abc

echo ""
echo "$ file-client read 87654321-4321-8765-cba9-987654321098"
docker-compose exec -T app file-client read 87654321-4321-8765-cba9-987654321098

echo ""
echo "3. Testing cli-client status command:"
echo "$ cli-client status"
docker-compose exec -T app cli-client status

echo ""
echo "4. Testing cli-client active-domains command:"
echo "$ cli-client active-domains"
docker-compose exec -T app cli-client active-domains

echo ""
echo "5. Testing cli-client flagged-domains command:"
echo "$ cli-client flagged-domains"
docker-compose exec -T app cli-client flagged-domains

echo ""
echo "6. Testing file-client with invalid UUID (should show error):"
echo "$ file-client stat invalid-uuid"
docker-compose exec -T app file-client stat invalid-uuid || echo "✅ Expected error occurred"

echo ""
echo "7. Testing file-client with non-existent UUID (should show error):"
echo "$ file-client stat 99999999-9999-9999-9999-999999999999"
docker-compose exec -T app file-client stat 99999999-9999-9999-9999-999999999999 || echo "✅ Expected error occurred"

echo ""
echo "8. Testing file-client output to file:"
echo "$ file-client --output /tmp/test_output.txt stat 12345678-1234-5678-9abc-123456789abc"
docker-compose exec -T app file-client --output /tmp/test_output.txt stat 12345678-1234-5678-9abc-123456789abc
echo "$ cat /tmp/test_output.txt"
docker-compose exec -T app cat /tmp/test_output.txt

echo ""
echo "====================================="
echo "All tests completed successfully!"
echo "====================================="