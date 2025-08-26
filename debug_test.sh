#!/bin/bash

echo "Starting containers..."
docker-compose up -d

echo "Waiting for database..."
until docker-compose exec -T db pg_isready -U user -d domains > /dev/null 2>&1; do
  echo "  Waiting for DB..."
  sleep 2
done

echo "Testing CLI directly in container..."
docker-compose exec -T app python test_cli_simple.py

echo "Testing if CLI file exists and is executable..."
docker-compose exec -T app ls -la cli.py
docker-compose exec -T app python -c "import cli.commands; print('CLI module imports successfully')"

echo "Testing basic CLI invocation..."
docker-compose exec -T app python -c "
from cli.commands import cli
from click.testing import CliRunner
runner = CliRunner()
result = runner.invoke(cli, ['--help'])
print('Exit code:', result.exit_code)
print('Output length:', len(result.output))
print('First 200 chars:', repr(result.output[:200]))
"