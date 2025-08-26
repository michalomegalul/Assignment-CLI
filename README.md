# Domain Management CLI

A comprehensive CLI tool for domain registration management with PostgreSQL backend and REST/gRPC API integration.
 

## Overview

This project implements a CLI application:
1. **File Client** - Retrieves and prints data from REST/gRPC backends
2. **Domain Management** - PostgreSQL database for domain lifecycle

## Features

### File Client
- **REST API Integration** - File operations via REST endpoints
- **gRPC Support** - Interface ready
- **UUID Validation** - Proper format checking
- **Flexible Output** - Console or file output options
- **Error Handling** - error reporting

### Domain Management System
- **PostgreSQL Database** - Advanced domain lifecycle management
- **Domain Flag System** - Track EXPIRED, OUTZONE, DELETE_CANDIDATE states
- **Time-based Constraints** - Prevent overlapping registrations
- **Advanced Queries** - Domain status reporting
- **Docker Integration** - Containerized environment

## Installation

### Quick Start with Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/michalomegalul/Assignment-CLI.git
cd Assignment-CLI

# Start services
docker-compose up -d

# Initialize test data
docker-compose exec app python init_script.py

# Run the CLI
docker-compose exec app python cli.py --help
```

### Local Installation

```bash
# Prerequisites: Python 3.7-3.10, PostgreSQL 9.6+

# Install dependencies
pip install -r requirements.txt

# Setup database
createdb -U postgres domains
psql -U postgres -d domains -f sql/schema.sql
psql -U postgres -d domains -f sql/seed.sql

# Configure environment
cp .env.example .env
# Edit .env with your database details

# Run CLI
python cli.py --help
```

## File Client Usage (Assignment Specification)

The `file-client` command implements the exact assignment requirements:

```bash
# Basic usage
python cli.py file-client [options] stat UUID
python cli.py file-client [options] read UUID

# Examples
python cli.py file-client stat 123e4567-e89b-12d3-a456-426614174000
python cli.py file-client --backend rest stat 123e4567-e89b-12d3-a456-426614174000
python cli.py file-client --backend rest --base-url http://api.example.com/ read 123e4567-e89b-12d3-a456-426614174000
python cli.py file-client --output /tmp/metadata.txt stat 123e4567-e89b-12d3-a456-426614174000
```

### File Client Options

| Option          | Default             | Description |
|--------         |---------            |-------------|
| `--backend`     | `grpc`              | Backend type: `grpc` or `rest` |
| `--grpc-server` | `localhost:50051`   | gRPC server host:port |
| `--base-url`    | `http://localhost/` | REST API base URL |
| `--output`      | `-`                 | Output file (- for stdout) |

### Commands

- **`stat`** - Prints file metadata
- **`read`** - Outputs file content

# Domain management commands
python cli.py status
python cli.py active-domains
python cli.py flagged-domains

# File client commands (matching assignment requirements exactly)
python cli.py file-client --help
python cli.py file-client stat UUID
python cli.py file-client read UUID
python cli.py file-client --backend=rest stat UUID
python cli.py file-client --base-url=http://example.com/ stat UUID
python cli.py file-client --output=output.txt read UUID
```

## Database Schema

### Tables

**`domain`**
```sql
- id (SERIAL PRIMARY KEY)
- fqdn (VARCHAR(255) NOT NULL)
- registered_at (TIMESTAMP WITH TIME ZONE)
- unregistered_at (TIMESTAMP WITH TIME ZONE)
- created_at, updated_at (TIMESTAMP WITH TIME ZONE)
```

**`domain_flag`**
```sql
- id (SERIAL PRIMARY KEY)
- domain_id (INTEGER REFERENCES domain(id))
- flag (VARCHAR(32)) -- EXPIRED, OUTZONE, DELETE_CANDIDATE
- valid_from, valid_to (TIMESTAMP WITH TIME ZONE)
```

## Testing

### Run All Tests

```bash
# Docker environment
docker-compose exec app pytest tests/ -v
#OR:
- `test_cli.py` - File client and database command tests
- `run_tests.sh` - Script to automate tests for debbuging
### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/domains

# API (for testing)
API_BASE_URL=http://localhost:8080

# Logging
LOG_LEVEL=INFO
```

## Project Structure

```
Assignment-CLI/
├── cli.py                 # Main CLI application
├── sql/
│   ├── schema.sql        # Database schema
│   └── seed.sql          # Test data
├── tests/
│   └── test_cli.py       # Unit tests
├── docker-compose.yml    # Container
├── Dockerfile           # Application container
├── requirements.txt     # Python dependencies
├── init_script.py       # Database initialization
└── README.md           # This file
```

### Logging

Enable logging for debugging:
```bash
python cli.py --verbose status
python cli.py --verbose file-client stat <uuid>