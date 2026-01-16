"""
Patient Service
Business logic for patient operations
Handles database queries and patient/visit management
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from datetime import date
from app.models.models import Patient, Person, Visit
from app.models.schemas import PatientResponse


class PatientService:
    """Service class for patient operations"""
    
    @staticmethod
    def get_patient_by_mrn(db: Session, mrn: str) -> Optional[Patient]:
        """
        Find a patient by their MRN
        
        Args:
            db: Database session
            mrn: Medical Record Number
            
        Returns:
            Patient object if found, None otherwise
        """
        return db.query(Patient).filter(Patient.mrn == mrn).first()
    
    @staticmethod
    def get_patient_by_id(db: Session, patient_id: int) -> Optional[Patient]:
        """
        Find a patient by their ID
        
        Args:
            db: Database session
            patient_id: Patient ID
            
        Returns:
            Patient object if found, None otherwise
        """
        return db.query(Patient).filter(Patient.id == patient_id).first()
    
    @staticmethod
    def create_patient(db: Session, mrn: str, first_name: str, 
                      last_name: str, birth_date: date) -> Patient:
        """
        Create a new patient and associated person record
        Person ID will match Patient ID (one-to-one relationship)
        
        Args:
            db: Database session
            mrn: Medical Record Number
            first_name: Patient's first name
            last_name: Patient's last name
            birth_date: Patient's date of birth
            
        Returns:
            Created Patient object
        """
        # Create patient
        patient = Patient(mrn=mrn)
        db.add(patient)
        db.flush()  # Get the patient ID without committing
        
        # Create person with same ID as patient
        person = Person(
            id=patient.id,
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date
        )
        db.add(person)
        db.commit()
        db.refresh(patient)
        
        print(f"Created new patient: MRN={mrn}, ID={patient.id}")
        return patient
    
    @staticmethod
    def update_person(db: Session, patient: Patient, first_name: str, 
                     last_name: str, birth_date: date) -> None:
        """
        Update person information for an existing patient
        Only updates if values have changed
        
        Args:
            db: Database session
            patient: Patient object whose person info to update
            first_name: New first name
            last_name: New last name
            birth_date: New birth date
        """
        person = patient.person
        updated = False
        
        if person.first_name != first_name:
            person.first_name = first_name
            updated = True
        
        if person.last_name != last_name:
            person.last_name = last_name
            updated = True
        
        if person.birth_date != birth_date:
            person.birth_date = birth_date
            updated = True
        
        if updated:
            db.commit()
            print(f"Updated person info for patient MRN={patient.mrn}")
    
    @staticmethod
    def get_visit_by_account_number(db: Session, visit_account_number: str) -> Optional[Visit]:
        """
        Find a visit by its account number
        
        Args:
            db: Database session
            visit_account_number: Unique visit identifier
            
        Returns:
            Visit object if found, None otherwise
        """
        return db.query(Visit).filter(Visit.visit_account_number == visit_account_number).first()
    
    @staticmethod
    def create_visit(db: Session, patient_id: int, visit_account_number: str,
                    visit_date: date, reason: str) -> Visit:
        """
        Create a new visit for a patient
        
        Args:
            db: Database session
            patient_id: ID of the patient
            visit_account_number: Unique visit identifier
            visit_date: Date of the visit
            reason: Reason for the visit
            
        Returns:
            Created Visit object
        """
        visit = Visit(
            patient_id=patient_id,
            visit_account_number=visit_account_number,
            visit_date=visit_date,
            reason=reason
        )
        db.add(visit)
        db.commit()
        db.refresh(visit)
        
        print(f"Created visit: {visit_account_number} for patient_id={patient_id}")
        return visit
    
    @staticmethod
    def update_visit(db: Session, visit: Visit, visit_date: date, reason: str) -> Visit:
        """
        Update an existing visit's information
        Only updates if values have changed
        
        Args:
            db: Database session
            visit: Visit object to update
            visit_date: New visit date
            reason: New reason for visit
            
        Returns:
            Updated Visit object
        """
        updated = False
        
        if visit.visit_date != visit_date:
            visit.visit_date = visit_date
            updated = True
        
        if visit.reason != reason:
            visit.reason = reason
            updated = True
        
        if updated:
            db.commit()
            db.refresh(visit)
            print(f"Updated visit: {visit.visit_account_number}")
        else:
            print(f"Visit {visit.visit_account_number} unchanged")
        
        return visit
    
    @staticmethod
    def get_patients_paginated(db: Session, page: int = 1, page_size: int = 10,
                               mrn: Optional[str] = None,
                               first_name: Optional[str] = None,
                               last_name: Optional[str] = None) -> Tuple[List[Patient], int]:
        """
        Get paginated list of patients with optional filtering
        
        Args:
            db: Database session
            page: Page number (1-indexed)
            page_size: Number of items per page
            mrn: Optional MRN filter (partial match)
            first_name: Optional first name filter (partial match)
            last_name: Optional last name filter (partial match)
            
        Returns:
            Tuple of (list of patients, total count)
        """
        query = db.query(Patient).join(Person)
        
        # Apply filters if provided
        if mrn:
            query = query.filter(Patient.mrn.ilike(f"%{mrn}%"))
        
        if first_name:
            query = query.filter(Person.first_name.ilike(f"%{first_name}%"))
        
        if last_name:
            query = query.filter(Person.last_name.ilike(f"%{last_name}%"))
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        patients = query.offset(offset).limit(page_size).all()
        
        return patients, total
