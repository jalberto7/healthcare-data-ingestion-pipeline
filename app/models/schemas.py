"""
Pydantic Schemas
Defines request/response models for API validation
These are different from database models - used for data validation
"""
from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional


class VisitRecord(BaseModel):
    """Schema for a single visit record in the ingestion payload"""
    mrn: str = Field(..., description="Medical Record Number - uniquely identifies a patient")
    first_name: str = Field(..., description="Patient's first name")
    last_name: str = Field(..., description="Patient's last name")
    birth_date: date = Field(..., description="Patient's date of birth")
    visit_account_number: str = Field(..., description="Unique visit identifier")
    visit_date: date = Field(..., description="Date of the visit")
    reason: str = Field(..., description="Reason for the visit")


class VisitResponse(BaseModel):
    """Response model for a visit"""
    id: int
    visit_account_number: str
    visit_date: date
    reason: str
    
    class Config:
        from_attributes = True  # Allows conversion from ORM models


class PersonResponse(BaseModel):
    """Response model for person demographic information"""
    first_name: str
    last_name: str
    birth_date: date
    
    class Config:
        from_attributes = True


class PatientResponse(BaseModel):
    """Response model for a patient with person and visits"""
    id: int
    mrn: str
    person: PersonResponse
    visits: List[VisitResponse] = []
    
    class Config:
        from_attributes = True


class PaginatedPatientResponse(BaseModel):
    """Response model for paginated patient list"""
    total: int = Field(..., description="Total number of patients")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    patients: List[PatientResponse]


class IngestResponse(BaseModel):
    """Response model for ingestion endpoint"""
    message: str
    records_received: int
    csv_filename: str
    task_id: str
