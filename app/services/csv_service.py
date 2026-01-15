"""
CSV Service
Handles CSV file creation and parsing
Converts JSON data to CSV and vice versa
"""
import csv
import os
from datetime import datetime
from typing import List, Dict
from app.models.schemas import VisitRecord
from app.config import settings


class CSVService:
    """Service class for CSV operations"""
    
    CSV_HEADERS = ['mrn', 'first_name', 'last_name', 'birth_date', 
                   'visit_account_number', 'visit_date', 'reason']
    
    def __init__(self):
        """Initialize CSV service and ensure upload directory exists"""
        self.upload_dir = settings.upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def create_csv_from_records(self, records: List[VisitRecord]) -> str:
        """
        Convert list of VisitRecord objects to CSV file
        
        Args:
            records: List of visit records to convert
            
        Returns:
            Path to the created CSV file
        """
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"patient_intake_{timestamp}.csv"
        filepath = os.path.join(self.upload_dir, filename)
        
        # Write CSV file
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.CSV_HEADERS)
            writer.writeheader()
            
            # Convert each record to dictionary and write
            for record in records:
                row = {
                    'mrn': record.mrn,
                    'first_name': record.first_name,
                    'last_name': record.last_name,
                    'birth_date': record.birth_date.isoformat(),  # Convert date to string
                    'visit_account_number': record.visit_account_number,
                    'visit_date': record.visit_date.isoformat(),
                    'reason': record.reason
                }
                writer.writerow(row)
        
        print(f"Created CSV file: {filepath} with {len(records)} records")
        return filepath
    
    def parse_csv_file(self, filepath: str) -> List[Dict]:
        """
        Parse CSV file and return list of dictionaries
        
        Args:
            filepath: Path to the CSV file to parse
            
        Returns:
            List of dictionaries, each representing a row
        """
        records = []
        
        with open(filepath, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                records.append(row)
        
        print(f"Parsed {len(records)} records from {filepath}")
        return records
