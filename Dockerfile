FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
    
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python generate_proto.py

RUN chmod +x file-client

ENV PATH="/app:${PATH}"

RUN useradd -m -u 1000 user && chown -R user:user /app
USER user

CMD ["python", "--help"]