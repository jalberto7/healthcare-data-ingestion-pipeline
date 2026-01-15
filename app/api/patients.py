"""
API Routes - Patient Endpoints
Handles GET /patients and GET /patients/<id> endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.models.schemas import PatientResponse, PaginatedPatientResponse
from app.db.database import get_db
from app.services.patient_service import PatientService

router = APIRouter()


@router.get("/patients", response_model=PaginatedPatientResponse)
async def get_patients(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    mrn: Optional[str] = Query(None, description="Filter by MRN (partial match)"),
    first_name: Optional[str] = Query(None, description="Filter by first name (partial match)"),
    last_name: Optional[str] = Query(None, description="Filter by last name (partial match)"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of patients
    
    Features:
    - Pagination (page and page_size parameters)
    - Filtering by MRN, first_name, last_name
    - Returns patient with person and visit information
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        mrn: Optional MRN filter
        first_name: Optional first name filter
        last_name: Optional last name filter
        db: Database session
        
    Returns:
        PaginatedPatientResponse with patients and pagination metadata
    """
    patients, total = PatientService.get_patients_paginated(
        db=db,
        page=page,
        page_size=page_size,
        mrn=mrn,
        first_name=first_name,
        last_name=last_name
    )
    
    return PaginatedPatientResponse(
        total=total,
        page=page,
        page_size=page_size,
        patients=patients
    )


@router.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: int, db: Session = Depends(get_db)):
    """
    Get a single patient by ID
    
    Includes:
    - Patient information (ID, MRN)
    - Person information (demographics)
    - All visits for this patient
    
    Args:
        patient_id: The patient ID
        db: Database session
        
    Returns:
        PatientResponse with complete patient information
        
    Raises:
        404: If patient not found
    """
    patient = PatientService.get_patient_by_id(db, patient_id)
    
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient with ID {patient_id} not found")
    
    return patient
