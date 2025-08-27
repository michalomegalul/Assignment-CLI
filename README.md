# Domain Management CLI

A comprehensive CLI tool for domain registration management with PostgreSQL backend and REST/gRPC API integration.
 

## Overview

This project implements a CLI application:
1. **File Client** - Fetches file metadata and contents from REST or gRPC backends.
2. **Domain Management** - PostgreSQL database for domain lifecycle

## Features

### File Client
- **REST API Integration** - File operations via REST endpoints
- **gRPC Support** - doesn't work had problem with importing grpc generated files tried it in different project so logic should work never worked with grpc but happy to learn
- **UUID Validation** - Proper format checking
- **Flexible Output** - Console or file output options
- **Error Handling** - error reporting

### Domain Management System
- **PostgreSQL Database** - Advanced domain lifecycle management
- **Domain Flag System** - Track EXPIRED, OUTZONE, DELETE_CANDIDATE states
- **Time-based Constraints** - Prevent overlapping
- **Advanced Queries** - Domain status reporting
- **Docker Integration** - Containerized environment

## Installation

### Quick Start with Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/michalomegalul/Assignment-CLI.git
cd Assignment-CLI

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start services
docker-compose up -d

# Initialize test data
docker-compose exec app python init_script.py

# Run the Commands directly
docker-compose exec app python file-client --help

# OR open a shell in the container
docker-compose exec app bash
file-client --help
```

### Local Installation

```bash
# Prerequisites: Python 3.7–3.10, PostgreSQL 9.6+

# Install dependencies
pip install -r requirements.txt

# Setup database
createdb -U postgres domains
psql -U postgres -d domains -f sql/schema.sql
psql -U postgres -d domains -f sql/seed.sql

# Configure environment
cp .env.example .env
# Edit .env with your database settings

# Initialize demo files
python helper_scripts/setup_demo.sh

# Run file-client
python -m file-client --help

```

## File Client Usage

The `file-client` command implements:

```bash
# Basic usage
file-client [options] stat UUID
file-client [options] read UUID

# Working examples with pre-loaded demo data
file-client stat 12345678-1234-5678-9abc-123456789abc
file-client read 87654321-4321-8765-cba9-987654321098
file-client stat 11111111-2222-3333-4444-555555555555

# With options
file-client --backend rest stat 12345678-1234-5678-9abc-123456789abc
file-client --base-url http://web:5000/ read 87654321-4321-8765-cba9-987654321098
file-client --output /tmp/metadata.txt stat 12345678-1234-5678-9abc-123456789abc
```

### File Client Options

| Option          | Default             | Description |
|--------         |---------            |-------------|
| `--backend`     | `rest`              | Backend type: `grpc` or `rest` |
| `--grpc-server` | `localhost:50051`   | gRPC server host:port |
| `--base-url`    | `http://web:5000/`  | REST API base URL |
| `--output`      | `-`                 | Output file (- for stdout) |

### Commands

- **`stat`** - Prints file metadata
- **`read`** - Outputs file content

# Domain management commands (separate from file-client)
cli-client status
cli-client active-domains  
cli-client flagged-domains

# File client commands (Assignment implementation)
file-client --help
file-client stat UUID
file-client read UUID
file-client --backend=rest stat UUID
file-client --base-url=http://web:5000/ stat UUID
file-client --output=output.txt read UUID

### Output to file
```bash
# Save metadata to file
$ file-client --output metadata.txt stat 12345678-1234-5678-9abc-123456789abc
$ cat metadata.txt

# Save content to file
$ file-client --output content.json read 87654321-4321-8765-cba9-987654321098
$ cat content.json
```
### Environment Configuration
```
# Development mode with verbose logging
APP_ENV=development LOG_LEVEL=debug file-client stat UUID

# Production mode (quiet - errors only)
APP_ENV=production file-client stat UUID

# Custom base URL
file-client --base-url http://localhost:5000/ stat UUID
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
sudo ./helper_scripts/run_tests.sh
```