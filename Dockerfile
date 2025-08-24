FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
    
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make CLI executable
RUN chmod +x cli.py

# Create non-root user
RUN useradd -m -u 1000 user && chown -R user:user /app
USER user

CMD ["python", "cli.py", "--help"]