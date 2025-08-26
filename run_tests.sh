#!/bin/bash
set -euo pipefail

echo "====================================="
echo "         Test Runner"
echo "====================================="

echo "[1/5] Stopping existing containers..."
docker-compose down -v || echo "No containers to stop."

echo "[2/5] Starting services..."
docker-compose up -d

echo "[3/5] Waiting for database to be ready..."
until docker-compose exec -T db pg_isready -U user -d domains > /dev/null 2>&1; do
  echo "  Waiting for DB..."
  sleep 2
done
echo "  Database is ready."

echo "[4/5] Initializing test data..."
docker-compose exec -T app python -m cli.init_db || {
  echo "Failed to initialize DB"
  exit 1
}

echo "[5/5] Running tests..."
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
echo "1. Testing CLI help command:"
echo "$ python cli.py --help"
docker-compose exec -T app python cli.py --help

echo ""
echo "2. Testing file-client help:"
echo "$ python cli.py file-client --help"
docker-compose exec -T app python cli.py file-client --help

echo ""
echo "3. Testing status command:"
echo "$ python cli.py status"
docker-compose exec -T app python cli.py status

echo ""
echo "4. Testing active-domains command:"
echo "$ python cli.py active-domains"
docker-compose exec -T app python cli.py active-domains

echo ""
echo "5. Testing flagged-domains command:"
echo "$ python cli.py flagged-domains"
docker-compose exec -T app python cli.py flagged-domains

echo ""
echo "6. Testing file-client with invalid UUID (should show error):"
echo "$ python cli.py file-client stat invalid-uuid"
docker-compose exec -T app python cli.py file-client stat invalid-uuid || echo "✓ Expected error occurred"

echo ""
echo "7. Testing file-client with valid UUID but no server (should show error):"
echo "$ python cli.py file-client --backend rest stat 123e4567-e89b-12d3-a456-426614174000"
docker-compose exec -T app python cli.py file-client --backend rest stat 123e4567-e89b-12d3-a456-426614174000 || echo "✓ Expected error occurred"

echo ""
echo "8. Testing gRPC backend (should show not implemented):"
echo "$ python cli.py file-client --backend grpc stat 123e4567-e89b-12d3-a456-426614174000"
docker-compose exec -T app python cli.py file-client --backend grpc stat 123e4567-e89b-12d3-a456-426614174000 || echo "✓ Expected error occurred"

echo ""
echo "====================================="
echo "All tests completed successfully!"
echo "====================================="