"""
S3 Service
Handles all interactions with AWS S3 (LocalStack)
Provides upload and download functionality for CSV files
"""
import boto3
import os
from botocore.client import Config
from boto3.s3.transfer import TransferConfig
from app.config import settings


class S3Service:
    """Service class for S3 operations"""
    
    def __init__(self):
        """
        Initialize S3 client
        Uses LocalStack endpoint for local development
        """
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
            config=Config(signature_version='s3v4')  # Signature version for compatibility
        )
        self.bucket_name = settings.s3_bucket_name
    
    def upload_file(self, file_path: str, object_name: str) -> bool:
        """
        Upload a file to S3 bucket with automatic multipart for large files
        
        Args:
            file_path: Local path to the file to upload
            object_name: Name to give the file in S3
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            file_size = os.path.getsize(file_path)
            
            # Use multipart upload for files > 10MB
            if file_size > 10 * 1024 * 1024:  # 10MB threshold
                print(f"Using multipart upload for large file ({file_size / (1024*1024):.2f} MB)")
                
                # Configure multipart upload
                config = TransferConfig(
                    multipart_threshold=10 * 1024 * 1024,  # 10MB
                    max_concurrency=10,
                    multipart_chunksize=10 * 1024 * 1024,  # 10MB chunks
                    use_threads=True
                )
                
                self.s3_client.upload_file(
                    file_path,
                    self.bucket_name,
                    object_name,
                    Config=config
                )
            else:
                # Regular upload for smaller files
                self.s3_client.upload_file(file_path, self.bucket_name, object_name)
            
            print(f"Successfully uploaded {file_path} to s3://{self.bucket_name}/{object_name}")
            return True
        except Exception as e:
            print(f"Error uploading to S3: {str(e)}")
            return False
    
    def download_file(self, object_name: str, file_path: str) -> bool:
        """
        Download a file from S3 bucket
        
        Args:
            object_name: Name of the file in S3
            file_path: Local path to save the downloaded file
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            self.s3_client.download_file(self.bucket_name, object_name, file_path)
            print(f"Successfully downloaded s3://{self.bucket_name}/{object_name} to {file_path}")
            return True
        except Exception as e:
            print(f"Error downloading from S3: {str(e)}")
            return False
    
    def list_files(self) -> list:
        """
        List all files in the S3 bucket
        
        Returns:
            List of file names in the bucket
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            return []
        except Exception as e:
            print(f"Error listing S3 files: {str(e)}")
            return []
