.PHONY: build up down logs start clean bootstrap-s3 db-init help

# Default target - show help
help:
	@echo "Healthcare Data Ingestion Pipeline - Makefile Commands"
	@echo "======================================================="
	@echo "make build        - Build all Docker containers"
	@echo "make up           - Start all services"
	@echo "make down         - Stop all services"
	@echo "make logs         - Display logs from all services"
	@echo "make start        - Complete system startup (build + bootstrap + up)"
	@echo "make clean        - Remove all containers, volumes, and uploads"
	@echo "make bootstrap-s3 - Create S3 bucket in LocalStack"
	@echo "make db-init      - Initialize database schema"

# Build all Docker containers
# This compiles the Dockerfile and prepares all images
build:
	@echo "Building Docker containers..."
	docker-compose build

# Start all services in detached mode
# Services will run in background
up:
	@echo "Starting all services..."
	docker-compose up -d
	@echo "Services are running. API available at http://localhost:8000"

# Stop all running services
down:
	@echo "Stopping all services..."
	docker-compose down

# Display logs from all services
# Use Ctrl+C to exit log view
logs:
	@echo "Displaying logs (Ctrl+C to exit)..."
	docker-compose logs -f

# Complete system startup with dependency bootstrapping
# This is the main command to get everything running
start: build
	@echo "Starting services..."
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 10
	@echo "Bootstrapping S3 bucket..."
	$(MAKE) bootstrap-s3
	@echo "Initializing database..."
	$(MAKE) db-init
	@echo ""
	@echo "=========================================="
	@echo "System is ready!"
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "=========================================="
	@echo ""
	@echo "To view logs: make logs"
	@echo "To stop: make down"

# Bootstrap S3 bucket in LocalStack
# Creates the patient-intake bucket if it doesn't exist
bootstrap-s3:
	@echo "Creating S3 bucket in LocalStack..."
	@docker exec healthcare_api python3 -c "import boto3; s3=boto3.client('s3', endpoint_url='http://localstack:4566', aws_access_key_id='test', aws_secret_access_key='test', region_name='us-east-1'); s3.create_bucket(Bucket='patient-intake'); print('Bucket created successfully!')" 2>/dev/null || echo "Bucket already exists or service not ready"

# Initialize database schema
# Runs Alembic migrations to create tables
db-init:
	@echo "Initializing database schema..."
	@docker exec healthcare_api python -c "from app.db.database import init_db; init_db()" || echo "Database already initialized"

# Clean up everything - containers, volumes, and local files
clean:
	@echo "Cleaning up..."
	docker-compose down -v
	rm -rf uploads/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@echo "Cleanup complete"

# Test the API with a sample request
test:
	@echo "Testing API with sample data..."
	curl -X POST http://localhost:8000/ingest \
		-H "Content-Type: application/json" \
		-d '[{"mrn":"MRN-1001","first_name":"John","last_name":"Doe","birth_date":"1990-02-14","visit_account_number":"VST-9001","visit_date":"2024-11-01","reason":"Annual Checkup"}]'
