# Healthcare Data Ingestion Pipeline

A production-ready microservice system for ingesting and processing healthcare data using FastAPI, PostgreSQL, Celery, and AWS LocalStack.

## 📋 Overview

This system implements a real-world backend data ingestion pipeline that:
- Accepts structured healthcare data via REST API
- Stores data as CSV in S3 (LocalStack)
- Processes data asynchronously using Celery workflows
- Persists data in normalized PostgreSQL database

## 🏗️ Architecture

```
Client → FastAPI → CSV File → LocalStack S3 → Celery Worker → PostgreSQL
```

### System Components

1. **FastAPI API Server** - HTTP REST API endpoints
2. **PostgreSQL Database** - Relational data storage
3. **Celery Worker** - Asynchronous task processing
4. **Redis** - Message broker for Celery
5. **LocalStack** - AWS S3 simulation for local development

## 🛠️ Technology Stack

- **Python 3.11**
- **FastAPI** - Modern web framework
- **PostgreSQL 15** - Relational database
- **SQLAlchemy** - ORM for database operations
- **Celery** - Distributed task queue
- **Redis** - Message broker
- **AWS LocalStack** - Local AWS cloud stack
- **Docker & Docker Compose** - Containerization
- **Makefile** - Automation

## 📦 Package Dependencies Explained

### Core Framework
- **fastapi** - High-performance web framework with automatic API documentation
- **uvicorn** - ASGI server to run FastAPI applications
- **pydantic** - Data validation using Python type annotations

### Database
- **sqlalchemy** - ORM that maps Python classes to database tables
- **psycopg2-binary** - PostgreSQL adapter for Python
- **alembic** - Database migration tool (for schema version control)

### Async Tasks
- **celery** - Distributed task queue for background processing
- **redis** - In-memory data store used as Celery message broker

### AWS Integration
- **boto3** - AWS SDK for Python (S3 operations)

### Data Processing
- **pandas** - Data manipulation and CSV processing

### Utilities
- **python-dotenv** - Load configuration from .env files
- **python-multipart** - Handle file uploads

## 📁 Project Structure

```
project-root/
├── app/                          # Main application code
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Configuration settings
│   ├── api/                     # API route handlers
│   │   ├── ingest.py           # POST /ingest endpoint
│   │   └── patients.py         # GET /patients endpoints
│   ├── services/                # Business logic layer
│   │   ├── csv_service.py      # CSV operations
│   │   ├── s3_service.py       # S3 operations
│   │   └── patient_service.py  # Patient data operations
│   ├── models/                  # Data models
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   └── schemas.py          # Pydantic validation schemas
│   └── db/                      # Database configuration
│       └── database.py         # DB connection and session
├── worker/                       # Celery worker
│   └── celery_app.py           # Workflow definitions
├── docker-compose.yml           # Multi-container orchestration
├── Dockerfile                   # Container image definition
├── Makefile                     # Automation commands
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## 🗄️ Database Schema

### Patient Table
- `id` (Primary Key) - Auto-increment integer
- `mrn` (Unique) - Medical Record Number
- `created_at` - Timestamp of record creation

### Person Table
- `id` (Primary Key = Patient.id) - Same as Patient ID
- `first_name` - Patient's first name
- `last_name` - Patient's last name
- `birth_date` - Patient's date of birth

### Visit Table
- `id` (Primary Key) - Auto-increment integer
- `visit_account_number` (Unique) - Visit identifier
- `patient_id` (Foreign Key) - Links to Patient
- `visit_date` - Date of visit
- `reason` - Reason for visit

### Key Relationships
- **Patient ↔ Person**: One-to-one (same ID)
- **Patient ↔ Visit**: One-to-many (one patient, multiple visits)

## 🚀 Setup and Installation

### Prerequisites
- Docker Desktop installed and running
- Make utility (pre-installed on macOS/Linux)
- 4GB+ RAM available for Docker

### Quick Start

1. **Clone and navigate to project:**
```bash
cd /Users/joemaralberto/Desktop/Programming/Python
```

2. **Create environment file:**
```bash
cp .env.example .env
```

3. **Start the entire system:**
```bash
make start
```

This single command will:
- Build all Docker containers
- Start all services
- Create S3 bucket in LocalStack
- Initialize database schema
- Display service URLs

**Expected output:**
```
==========================================
System is ready!
API: http://localhost:8000
API Docs: http://localhost:8000/docs
==========================================
```

## 📝 Makefile Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make build` | Build all Docker containers |
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | Display logs (Ctrl+C to exit) |
| `make start` | Complete system startup ⭐ |
| `make clean` | Remove all containers and volumes |
| `make test` | Run sample API test |

## 🔌 API Endpoints

### 1. POST /ingest
Ingest patient visit data.

**Request:**
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '[
    {
      "mrn": "MRN-1001",
      "first_name": "John",
      "last_name": "Doe",
      "birth_date": "1990-02-14",
      "visit_account_number": "VST-9001",
      "visit_date": "2024-11-01",
      "reason": "Annual Checkup"
    }
  ]'
```

**Response:**
```json
{
  "message": "Data ingestion started successfully",
  "records_received": 1,
  "csv_filename": "patient_intake_20240101_120000.csv",
  "task_id": "abc-123-def-456"
}
```

### 2. GET /patients
List all patients with pagination and filtering.

**Request:**
```bash
# Basic pagination
curl "http://localhost:8000/patients?page=1&page_size=10"

# With filters
curl "http://localhost:8000/patients?mrn=MRN-1001"
curl "http://localhost:8000/patients?first_name=John&last_name=Doe"
```

**Response:**
```json
{
  "total": 1,
  "page": 1,
  "page_size": 10,
  "patients": [
    {
      "id": 1,
      "mrn": "MRN-1001",
      "person": {
        "first_name": "John",
        "last_name": "Doe",
        "birth_date": "1990-02-14"
      },
      "visits": [
        {
          "id": 1,
          "visit_account_number": "VST-9001",
          "visit_date": "2024-11-01",
          "reason": "Annual Checkup"
        }
      ]
    }
  ]
}
```

### 3. GET /patients/{id}
Retrieve a single patient by ID.

**Request:**
```bash
curl http://localhost:8000/patients/1
```

**Response:** Same structure as single patient in list above.

## 📚 Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These interfaces allow you to:
- View all endpoints
- See request/response schemas
- Test APIs directly in the browser

## 🔍 Verification Steps

### 1. Verify S3 Upload

Check files in LocalStack S3:
```bash
docker exec healthcare_api aws --endpoint-url=http://localstack:4566 s3 ls s3://patient-intake
```

Download a file to verify:
```bash
docker exec healthcare_api aws --endpoint-url=http://localstack:4566 s3 cp s3://patient-intake/patient_intake_20240101_120000.csv /tmp/
docker exec healthcare_api cat /tmp/patient_intake_20240101_120000.csv
```

### 2. Verify Workflow Execution

View Celery worker logs:
```bash
docker logs healthcare_worker -f
```

Look for:
- `[WORKFLOW START]` - Workflow initiated
- `[STEP 1] Downloading CSV from S3...` - S3 download
- `[STEP 2] Parsing CSV file...` - CSV parsing
- `[STEP 3] Processing records...` - Data processing
- `[WORKFLOW COMPLETE]` - Success

### 3. Verify Database Records

Connect to PostgreSQL:
```bash
docker exec -it healthcare_postgres psql -U postgres -d healthcaredb
```

Run queries:
```sql
-- Check patients
SELECT * FROM patients;

-- Check persons
SELECT * FROM persons;

-- Check visits
SELECT * FROM visits;

-- Join query - patients with person info
SELECT p.id, p.mrn, pe.first_name, pe.last_name, pe.birth_date
FROM patients p
JOIN persons pe ON p.id = pe.id;

-- Exit psql
\q
```

## 🧪 Testing Workflow

### Test Case 1: New Patient
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '[
    {
      "mrn": "MRN-2001",
      "first_name": "Jane",
      "last_name": "Smith",
      "birth_date": "1985-05-20",
      "visit_account_number": "VST-2001",
      "visit_date": "2024-11-15",
      "reason": "Flu Symptoms"
    }
  ]'
```

**Expected Result:**
- New patient created
- New person record created
- New visit record created

### Test Case 2: Existing Patient (Update)
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '[
    {
      "mrn": "MRN-2001",
      "first_name": "Jane",
      "last_name": "Smith-Johnson",
      "birth_date": "1985-05-20",
      "visit_account_number": "VST-2002",
      "visit_date": "2024-12-01",
      "reason": "Follow-up"
    }
  ]'
```

**Expected Result:**
- Patient already exists (same MRN)
- Person info updated (last name changed)
- New visit added to existing patient

### Test Case 3: Multiple Visits for Same Patient
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '[
    {
      "mrn": "MRN-3001",
      "first_name": "Bob",
      "last_name": "Wilson",
      "birth_date": "1975-08-10",
      "visit_account_number": "VST-3001",
      "visit_date": "2024-10-01",
      "reason": "Physical Exam"
    },
    {
      "mrn": "MRN-3001",
      "first_name": "Bob",
      "last_name": "Wilson",
      "birth_date": "1975-08-10",
      "visit_account_number": "VST-3002",
      "visit_date": "2024-10-15",
      "reason": "Lab Results Review"
    }
  ]'
```

**Expected Result:**
- One patient created
- One person record
- Two visit records for same patient

## 🔧 Business Logic Rules

### MRN Deduplication
- **MRN is unique** per patient
- If MRN exists: Update person info + add new visit
- If MRN doesn't exist: Create new patient + person + visit

### Person Updates
- System checks if first_name, last_name, or birth_date changed
- Only updates if values are different
- Updates are atomic (all or nothing)

### Visit Creation
- **Always insert** new visit records (never update)
- Each visit has unique `visit_account_number`
- Multiple visits per patient supported
- Foreign key ensures data integrity

### Idempotency
- Workflow can be safely re-run
- Database constraints prevent duplicates
- Errors in one record don't stop processing others

## 🐛 Troubleshooting

### Issue: Services not starting
```bash
# Check if ports are already in use
lsof -i :8000  # FastAPI
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :4566  # LocalStack

# Stop conflicting services or change ports in docker-compose.yml
```

### Issue: Database connection error
```bash
# Wait for PostgreSQL to be ready
docker logs healthcare_postgres

# Manually initialize database
make db-init
```

### Issue: S3 bucket not found
```bash
# Recreate S3 bucket
make bootstrap-s3

# Verify bucket exists
docker exec healthcare_api aws --endpoint-url=http://localstack:4566 s3 ls
```

### Issue: Celery worker not processing
```bash
# Check worker logs
docker logs healthcare_worker

# Restart worker
docker restart healthcare_worker

# Check Redis connection
docker exec healthcare_redis redis-cli ping
```

### View all logs
```bash
make logs
```

## 🧹 Cleanup

Remove all containers and data:
```bash
make clean
```

This removes:
- All Docker containers
- All Docker volumes (database data)
- Local upload files
- Python cache files

## 📸 Screenshots / Logs

### Successful Workflow Execution
```
[WORKFLOW START] Processing CSV: patient_intake_20240101_120000.csv
[STEP 1] Downloading CSV from S3...
Successfully downloaded s3://patient-intake/patient_intake_20240101_120000.csv
[STEP 2] Parsing CSV file...
Found 3 records to process
[STEP 3] Processing records...
  Processing record 1/3: MRN=MRN-1001
    Creating new patient...
    Created new patient: MRN=MRN-1001, ID=1
    Creating visit: VST-9001
  Processing record 2/3: MRN=MRN-1001
    Patient exists (ID=1), updating person info...
    Creating visit: VST-9002
  Processing record 3/3: MRN=MRN-2001
    Creating new patient...
    Created new patient: MRN=MRN-2001, ID=2
    Creating visit: VST-2001
[WORKFLOW COMPLETE]
  Patients created: 2
  Patients updated: 1
  Visits created: 3
  Errors: 0
```

## 🎯 Key Features Implemented

✅ FastAPI with automatic OpenAPI documentation  
✅ PostgreSQL with normalized schema  
✅ SQLAlchemy ORM with relationships  
✅ Celery async task processing  
✅ LocalStack S3 integration  
✅ CSV file processing  
✅ Pagination and filtering  
✅ Docker containerization  
✅ Makefile automation  
✅ MRN deduplication logic  
✅ Idempotent workflows  
✅ Error handling  
✅ Logging and monitoring  
✅ Health check endpoints  

## 📞 Support

For issues or questions:
1. Check logs: `make logs`
2. Review troubleshooting section above
3. Verify all services are running: `docker ps`

## 🎓 Learning Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Celery**: https://docs.celeryq.dev/
- **Docker**: https://docs.docker.com/
- **LocalStack**: https://docs.localstack.cloud/

---

**Built for Technical Assessment** | **Production-Ready Architecture**
