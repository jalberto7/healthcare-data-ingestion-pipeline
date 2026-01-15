"""
Database Models
Defines the schema for Patient, Person, and Visit tables
Uses SQLAlchemy ORM for object-relational mapping
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Patient(Base):
    """
    Patient Table
    Represents a unique patient identified by MRN (Medical Record Number)
    MRN must be unique across all patients
    """
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    mrn = Column(String, unique=True, nullable=False, index=True)  # Medical Record Number - unique identifier
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Automatically set on creation
    
    # Relationships
    # one-to-one with Person (same ID)
    person = relationship("Person", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    # one-to-many with Visit
    visits = relationship("Visit", back_populates="patient", cascade="all, delete-orphan")


class Person(Base):
    """
    Person Table
    Stores demographic information about a patient
    Person ID matches Patient ID (one-to-one relationship)
    """
    __tablename__ = "persons"
    
    id = Column(Integer, ForeignKey("patients.id"), primary_key=True)  # Same as Patient ID
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False, index=True)  # Indexed for filtering
    birth_date = Column(Date, nullable=False)
    
    # Relationship back to Patient
    patient = relationship("Patient", back_populates="person")


class Visit(Base):
    """
    Visit Table
    Represents a patient visit/encounter
    Each visit is uniquely identified by visit_account_number
    Multiple visits can belong to one patient
    """
    __tablename__ = "visits"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    visit_account_number = Column(String, unique=True, nullable=False, index=True)  # Unique visit identifier
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)  # Links to Patient
    visit_date = Column(Date, nullable=False)
    reason = Column(String, nullable=False)
    
    # Relationship back to Patient
    patient = relationship("Patient", back_populates="visits")
