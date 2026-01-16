"""
Celery Application and Workflow
Handles asynchronous processing of CSV files from S3
"""
from celery import Celery
from sqlalchemy.orm import Session
from datetime import datetime
import os
import sys

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


@celery_app.task(name="process_csv_workflow")
def process_csv_workflow(csv_filename: str):
    """
    Main workflow task to process CSV file from S3
    
    This is an idempotent workflow that:
    1. Downloads CSV from S3
    2. Parses each row
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
        
        # Step 2: Parse CSV file
        print("[STEP 2] Parsing CSV file...")
        csv_service = CSVService()
        records = csv_service.parse_csv_file(local_filepath)
        print(f"Found {len(records)} records to process")
        
        # Step 3: Process each record
        print("[STEP 3] Processing records...")
        patients_created = 0
        patients_updated = 0
        visits_created = 0
        visits_updated = 0
        errors = []
        
        for idx, row in enumerate(records, 1):
            try:
                print(f"\n  Processing record {idx}/{len(records)}: MRN={row['mrn']}")
                
                # Parse dates
                birth_date = datetime.strptime(row['birth_date'], '%Y-%m-%d').date()
                visit_date = datetime.strptime(row['visit_date'], '%Y-%m-%d').date()
                
                # Check if patient already exists
                patient = PatientService.get_patient_by_mrn(db, row['mrn'])
                
                if patient:
                    # Patient exists - update person info
                    print(f"    Patient exists (ID={patient.id}), updating person info...")
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
                    print(f"    Creating new patient...")
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
                    print(f"    Visit exists ({row['visit_account_number']}), updating...")
                    visit = PatientService.update_visit(
                        db=db,
                        visit=visit,
                        visit_date=visit_date,
                        reason=row['reason']
                    )
                    visits_updated += 1
                else:
                    # Visit doesn't exist - create new visit
                    print(f"    Creating new visit: {row['visit_account_number']}")
                    visit = PatientService.create_visit(
                        db=db,
                        patient_id=patient.id,
                        visit_account_number=row['visit_account_number'],
                        visit_date=visit_date,
                        reason=row['reason']
                    )
                    visits_created += 1
                
            except Exception as e:
                error_msg = f"Error processing record {idx} (MRN={row.get('mrn', 'unknown')}): {str(e)}"
                print(f"    ERROR: {error_msg}")
                errors.append(error_msg)
                # Continue processing other records even if one fails
                continue
        
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
            "total_records": len(records),
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
