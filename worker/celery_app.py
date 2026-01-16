"""
Celery Application and Workflow
Handles asynchronous processing of CSV files from S3
"""
from celery import Celery, current_task
from sqlalchemy.orm import Session
from datetime import datetime
import os
import sys
import pandas as pd

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings
from app.db.database import SessionLocal
from app.services.s3_service import S3Service
from app.services.csv_service import CSVService
from app.services.patient_service import PatientService

# Initialize Celery application
celery_app = Celery(
    "healthcare_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


@celery_app.task(name="process_csv_workflow", bind=True)
def process_csv_workflow(self, csv_filename: str):
    """
    Main workflow task to process CSV file from S3 with chunked processing
    
    This is an idempotent workflow that:
    1. Downloads CSV from S3
    2. Parses CSV in chunks (handles large files efficiently)
    3. For each patient (identified by MRN):
       - If MRN exists: update person info, add new visit
       - If MRN doesn't exist: create patient, person, and visit
    
    Args:
        csv_filename: Name of the CSV file in S3 bucket
        
    Returns:
        Dictionary with processing results
    """
    print(f"[WORKFLOW START] Processing CSV: {csv_filename}")
    
    db = SessionLocal()
    
    try:
        # Step 1: Download CSV from S3
        print("[STEP 1] Downloading CSV from S3...")
        s3_service = S3Service()
        local_filepath = os.path.join(settings.upload_dir, f"downloaded_{csv_filename}")
        
        download_success = s3_service.download_file(csv_filename, local_filepath)
        if not download_success:
            raise Exception(f"Failed to download {csv_filename} from S3")
        
        # Step 2: Get total record count for progress tracking
        print("[STEP 2] Analyzing CSV file...")
        total_records = sum(1 for _ in open(local_filepath)) - 1  # Subtract header
        print(f"Found {total_records} records to process")
        
        # Step 3: Process records in chunks for memory efficiency
        print("[STEP 3] Processing records in chunks...")
        CHUNK_SIZE = 500  # Process 500 records at a time
        
        patients_created = 0
        patients_updated = 0
        visits_created = 0
        visits_updated = 0
        errors = []
        processed_count = 0
        
        # Process CSV in chunks using pandas
        for chunk_num, chunk_df in enumerate(pd.read_csv(local_filepath, chunksize=CHUNK_SIZE), 1):
            print(f"\n[CHUNK {chunk_num}] Processing {len(chunk_df)} records...")
            
            for idx, row in chunk_df.iterrows():
                processed_count += 1
                try:
                    # Update progress every 100 records
                    if processed_count % 100 == 0:
                        progress = int((processed_count / total_records) * 100)
                        self.update_state(
                            state='PROGRESS',
                            meta={
                                'current': processed_count,
                                'total': total_records,
                                'percent': progress,
                                'patients_created': patients_created,
                                'patients_updated': patients_updated,
                                'visits_created': visits_created,
                                'visits_updated': visits_updated
                            }
                        )
                        print(f"  Progress: {progress}% ({processed_count}/{total_records})")
                    
                    # Parse dates using pandas
                    birth_date = pd.to_datetime(row['birth_date']).date()
                    visit_date = pd.to_datetime(row['visit_date']).date()
                
                    # Check if patient already exists
                    patient = PatientService.get_patient_by_mrn(db, row['mrn'])
                    
                    if patient:
                        # Patient exists - update person info
                        PatientService.update_person(
                            db=db,
                            patient=patient,
                            first_name=row['first_name'],
                            last_name=row['last_name'],
                            birth_date=birth_date
                        )
                        patients_updated += 1
                    else:
                        # Patient doesn't exist - create new patient and person
                        patient = PatientService.create_patient(
                            db=db,
                            mrn=row['mrn'],
                            first_name=row['first_name'],
                            last_name=row['last_name'],
                            birth_date=birth_date
                        )
                        patients_created += 1
                    
                    # Check if visit exists by visit_account_number
                    visit = PatientService.get_visit_by_account_number(db, row['visit_account_number'])
                    
                    if visit:
                        # Visit exists - update visit information
                        visit = PatientService.update_visit(
                            db=db,
                            visit=visit,
                            visit_date=visit_date,
                            reason=row['reason']
                        )
                        visits_updated += 1
                    else:
                        # Visit doesn't exist - create new visit
                        visit = PatientService.create_visit(
                            db=db,
                            patient_id=patient.id,
                            visit_account_number=row['visit_account_number'],
                            visit_date=visit_date,
                            reason=row['reason']
                        )
                        visits_created += 1
                    
                except Exception as e:
                    error_msg = f"Error processing record {processed_count} (MRN={row.get('mrn', 'unknown')}): {str(e)}"
                    print(f"    ERROR: {error_msg}")
                        errors.append(error_msg)
                    # Continue processing other records even if one fails
                    continue
            
            # Commit after each chunk to free up memory
            db.commit()
            print(f"[CHUNK {chunk_num}] Committed changes to database")
        
        # Step 4: Cleanup - remove downloaded file
        try:
            os.remove(local_filepath)
            print(f"\n[CLEANUP] Removed temporary file: {local_filepath}")
        except Exception as e:
            print(f"[CLEANUP] Warning: Could not remove temp file: {str(e)}")
        
        # Return results
        result = {
            "status": "completed",
            "csv_filename": csv_filename,
            "total_records": total_records,
            "processed_records": processed_count,
            "patients_created": patients_created,
            "patients_updated": patients_updated,
            "visits_created": visits_created,
            "visits_updated": visits_updated,
            "errors": errors,
            "error_count": len(errors)
        }
        
        print(f"\n[WORKFLOW COMPLETE]")
        print(f"  Patients created: {patients_created}")
        print(f"  Patients updated: {patients_updated}")
        print(f"  Visits created: {visits_created}")
        print(f"  Errors: {len(errors)}")
        
        return result
        
    except Exception as e:
        error_msg = f"Workflow failed: {str(e)}"
        print(f"\n[WORKFLOW FAILED] {error_msg}")
        return {
            "status": "failed",
            "csv_filename": csv_filename,
            "error": error_msg
        }
    
    finally:
        db.close()


# Task to check workflow status
@celery_app.task(name="get_task_status")
def get_task_status(task_id: str):
    """
    Get the status of a task by its ID
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Task status information
    """
    task_result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }
