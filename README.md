# Domain Management CLI

A comprehensive CLI tool for domain registration management with PostgreSQL backend and REST API integration.

**Author:** michalomegalul  
**Version:** 1.0.0  
**Created:** 2025-08-24 19:26:21 UTC

## Features

- **PostgreSQL Database** with advanced domain lifecycle management
- **REST API Client** for file operations  
- **Domain Flag System** (EXPIRED, OUTZONE, DELETE_CANDIDATE)
- **Advanced Queries** with proper constraint handling
- **Docker Integration** for easy deployment
- **CLI Interface** with comprehensive commands
- **Interactive Data Generator** with random domain names

## Installation Options

Choose your preferred installation method:

### Option 1: Docker Installation (Recommended)

Perfect for isolated environment and quick setup.

#### Prerequisites
- Docker and Docker Compose

#### Steps

1. **Clone the repository:**
```bash
git clone https://github.com/michalomegalul/ulohapython23.git
cd ulohapython23
```

2. **Start services:**
```bash
docker-compose up -d
```

3. **Enter the application container:**
```bash
docker-compose exec app bash
```

4. **Initialize database with interactive setup:**
```bash
python init_data.py
```

5. **Verify installation:**
```bash
python -m cli.commands status
```

#### Usage in Docker
All commands run inside the container:
```bash
# Already inside container after: docker-compose exec app bash
python -m cli.commands active-domains
python -m cli.commands file-client --help
```

---

### Option 2: Local Installation (or use installation.bat)


#### Prerequisites
- Python 3.7-3.10
- PostgreSQL 9.6+ (running locally)

#### Steps

1. **Clone the repository:**
```bash
git clone https://github.com/michalomegalul/ulohapython23.git
cd ulohapython23
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Setup PostgreSQL database:**
```bash
# Create database (adjust connection details as needed)
createdb -U postgres domains

# Apply schema
psql -U postgres -d domains -f sql/schema.sql
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your database connection details
```

5. **Initialize database with interactive setup:**
```bash
python init_data.py
```

6. **Verify installation:**
```bash
python -m cli.commands status
```

#### Usage Locally
Commands run directly on your system:
```bash
python -m cli.commands active-domains
python -m cli.commands file-client --help
```

## Interactive Database Initialization

Both installation methods include an interactive script to populate your database:

```python name=init_data.py
#!/usr/bin/env python3
"""
Interactive Database Initialization Script

Allows users to populate the database with test data including
random domain names and various flag combinations.
"""

```

## Running Tests

### Test Structure

```bash
tests/
├── test_database.py        # Database operation tests
├── test_file_client.py     # File client tests
├── test_cli.py            # CLI command tests
└── test_integration.py    # End-to-end tests
```

### Running Tests - Docker Installation

```bash
# Enter container
docker-compose exec app bash

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_database.py -v

# Run with coverage
pytest tests/ --cov=cli --cov-report=html

# Run tests with output
pytest tests/ -v -s
```

### Running Tests - Local Installation

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_database.py -v

# Run with coverage
pytest tests/ --cov=cli --cov-report=html

# Run tests matching pattern
pytest tests/ -k "test_database" -v
```

### Sample Test Files

```python name=tests/test_database.py
import pytest
from unittest.mock import patch, MagicMock
from cli.database import DatabaseManager


class TestDatabaseManager:
    """Test database operations"""
    
    @patch('cli.database.psycopg2.connect')
    def test_get_active_domains(self, mock_connect):
        """Test querying active domains"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock query results
        mock_cursor.fetchall.return_value = [
            ('example.com',),
            ('test.org',),
            ('active-domain.net',)
        ]
        
        db = DatabaseManager()
        result = db.get_active_domains()
        
        assert len(result) == 3
        assert 'example.com' in result
        assert 'test.org' in result
        mock_cursor.execute.assert_called_once()
    
    @patch('cli.database.psycopg2.connect')
    def test_get_flagged_domains(self, mock_connect):
        """Test querying flagged domains"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_cursor.fetchall.return_value = [('flagged-domain.org',)]
        
        db = DatabaseManager()
        result = db.get_flagged_domains()
        
        assert len(result) == 1
        assert 'flagged-domain.org' in result
```

```python name=tests/test_file_client.py
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from cli.file_client import file_client


class TestFileClient:
    """Test file client functionality"""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    def test_help_command(self):
        """Test help command shows usage"""
        result = self.runner.invoke(file_client, ['--help'])
        
        assert result.exit_code == 0
        assert 'File client for REST/gRPC operations' in result.output
        assert 'stat' in result.output
        assert 'read' in result.output
    
    @patch('cli.file_client.requests.get')
    def test_stat_rest_success(self, mock_get):
        """Test successful stat command with REST backend"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'test.txt',
            'size': 1234,
            'mimetype': 'text/plain',
            'create_datetime': '2025-08-24T19:26:21Z'
        }
        mock_get.return_value = mock_response
        
        result = self.runner.invoke(file_client, [
            '--backend', 'rest',
            'stat', 
            '123e4567-e89b-12d3-a456-426614174000'
        ])
        
        assert result.exit_code == 0
        assert 'Name: test.txt' in result.output
        assert '1234 bytes' in result.output
    
    @patch('cli.file_client.requests.get')
    def test_stat_rest_not_found(self, mock_get):
        """Test stat command when file not found"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = self.runner.invoke(file_client, [
            '--backend', 'rest',
            'stat', 
            '123e4567-e89b-12d3-a456-426614174000'
        ])
        
        assert result.exit_code == 1
        assert 'File not found' in result.output
```

## Usage Examples

### Docker Installation Examples

```bash
# Start everything
docker-compose up -d

# Initialize with random data
docker-compose exec app python init_data.py

# Use CLI tools
docker-compose exec app python -m cli.commands status
docker-compose exec app python -m cli.commands active-domains

# File operations
docker-compose exec app python -m cli.commands file-client stat 123e4567-e89b-12d3-a456-426614174000

# Run tests
docker-compose exec app pytest tests/ -v

# Access database directly
docker-compose exec db psql -U user -d domains
```

### Local Installation Examples

```bash
# Initialize with interactive setup
python init_data.py

# Check status
python -m cli.commands status

# Query domains
python -m cli.commands active-domains
python -m cli.commands flagged-domains

# File client operations
python -m cli.commands file-client --backend rest stat 123e4567-e89b-12d3-a456-426614174000
python -m cli.commands file-client --output /tmp/content.txt read 123e4567-e89b-12d3-a456-426614174000

# Run tests
pytest tests/ -v --cov=cli
```

## Configuration Files

### Docker Compose
```yaml name=docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:13
    restart: always
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: domains
    ports:
      - "5432:5432"
    volumes:
      - ./sql/schema.sql:/docker-entrypoint-initdb.d/1_schema.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d domains"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    build: .
    volumes:
      - .:/app
    working_dir: /app
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
    command: tail -f /dev/null
```

### Environment Configuration
```env name=.env.example
# Database configuration
DATABASE_URL=postgresql://user:password@db:5432/domains

# For local installation, use:
# DATABASE_URL=postgresql://user:password@localhost:5432/domains

# API endpoints
API_BASE_URL=http://localhost:8080

# App configuration
APP_VERSION=1.0.0
APP_AUTHOR=michalomegalul
```

## Troubleshooting

### Docker Installation Issues

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs db
docker-compose logs app

# Restart services
docker-compose restart

# Rebuild app container
docker-compose build app
```

### Local Installation Issues

```bash
# Check PostgreSQL connection
psql postgresql://user:password@localhost:5432/domains -c "SELECT 1;"

# Verify Python environment
python --version
pip list | grep -E "(click|psycopg2|requests)"

# Test database connection
python -c "from cli.database import DatabaseManager; db = DatabaseManager(); print('Connection OK')"
```

### Test Issues

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run single test with debug output
pytest tests/test_database.py::TestDatabaseManager::test_get_active_domains -v -s

# Check test coverage
pytest tests/ --cov=cli --cov-report=term-missing
```

## License

This project is part of a Python assignment and is intended for educational purposes.

---

**Last Updated:** 2025-08-24 19:26:21 UTC  
**Maintainer:** michalomegalul