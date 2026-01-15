# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Install system dependencies
# - gcc, postgresql-dev: Required for compiling psycopg2
# - curl: Useful for health checks
# - awscli: AWS CLI for S3 operations
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    curl \
    awscli \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Docker layer caching - if requirements don't change, this layer is cached)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory for CSV files
RUN mkdir -p /app/uploads

# Expose port 8000 for FastAPI
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
