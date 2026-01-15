"""
API Routes - Ingestion Endpoint
Handles the POST /ingest endpoint for data ingestion
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os

from app.models.schemas import VisitRecord, IngestResponse
from app.db.database import get_db
from app.services.csv_service import CSVService
from app.services.s3_service import S3Service
from worker.celery_app import process_csv_workflow

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_data(records: List[VisitRecord], db: Session = Depends(get_db)):
    """
    Ingest patient visit data
    
    Flow:
    1. Receive JSON array of visit records
    2. Convert to CSV file
    3. Upload CSV to S3 (LocalStack)
    4. Trigger Celery workflow to process the CSV
    5. Return confirmation with task ID
    
    Args:
        records: List of visit records
        db: Database session (dependency injection)
        
    Returns:
        IngestResponse with task ID and file information
    """
    try:
        # Step 1: Create CSV file from records
        csv_service = CSVService()
        csv_filepath = csv_service.create_csv_from_records(records)
        csv_filename = os.path.basename(csv_filepath)
        
        # Step 2: Upload CSV to S3
        s3_service = S3Service()
        upload_success = s3_service.upload_file(csv_filepath, csv_filename)
        
        if not upload_success:
            raise HTTPException(status_code=500, detail="Failed to upload CSV to S3")
        
        # Step 3: Trigger Celery workflow
        # This runs asynchronously in the background
        task = process_csv_workflow.delay(csv_filename)
        
        return IngestResponse(
            message="Data ingestion started successfully",
            records_received=len(records),
            csv_filename=csv_filename,
            task_id=task.id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
