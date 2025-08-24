set -e

echo "Test Runner"
echo "#########################################"
# Stop existing containers
echo "Stopping existing containers..."
docker-compose down -v
# Start services

echo "Starting services..."
docker-compose -f docker-compose.yml up -d

# Wait for database
echo "Waiting for database to be ready..."
until docker-compose exec db pg_isready -U user -d domains; do
  sleep 2
done

# Initialize test data
echo "Initializing test data..."
docker-compose -f docker-compose.yml exec app python init_script.py

# Run tests
echo "Running tests..."
docker-compose -f docker-compose.yml exec app python -m pytest tests/ -v

# Show final status
echo "Final status check..."
docker-compose -f docker-compose.yml exec app python cli.py status

echo "All tests completed!"