"""
Main FastAPI Application
Entry point for the API server
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import ingest, patients
from app.db.database import init_db

# Create FastAPI application instance
app = FastAPI(
    title="Healthcare Data Ingestion API",
    description="API for ingesting and managing patient visit data",
    version="1.0.0"
)

# CORS middleware - allows requests from any origin
# In production, you would restrict this to specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router, tags=["Ingestion"])
app.include_router(patients.router, tags=["Patients"])


@app.on_event("startup")
async def startup_event():
    """
    Runs when the application starts
    Initializes the database schema
    """
    print("Starting up...")
    init_db()
    print("Application ready!")


@app.get("/")
async def root():
    """
    Root endpoint - health check
    """
    return {
        "message": "Healthcare Data Ingestion API",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    Used by Docker and monitoring systems
    """
    return {"status": "healthy"}
