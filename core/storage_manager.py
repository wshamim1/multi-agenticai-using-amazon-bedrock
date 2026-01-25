"""
S3 Storage Management Module
Handles S3 bucket operations, file uploads, and data management
"""

import os
import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages S3 storage operations"""
    
    def __init__(self, s3_client, region: str):
        """
        Initialize Storage Manager
        
        Args:
            s3_client: Boto3 S3 client
            region: AWS region
        """
        self.s3_client = s3_client
        self.region = region
    
    def create_bucket(self, bucket_name: str) -> bool:
        """
        Create S3 bucket if it doesn't exist
        
        Args:
            bucket_name: Name of the S3 bucket
            
        Returns:
            True if bucket was created or already exists
        """
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"S3 bucket '{bucket_name}' already exists")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    if self.region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    
                    logger.info(f"Created S3 bucket '{bucket_name}' in region '{self.region}'")
                    
                    # Enable versioning
                    self.s3_client.put_bucket_versioning(
                        Bucket=bucket_name,
                        VersioningConfiguration={'Status': 'Enabled'}
                    )
                    logger.info(f"Enabled versioning for bucket '{bucket_name}'")
                    
                    return True
                    
                except ClientError as create_error:
                    logger.error(f"Failed to create S3 bucket '{bucket_name}': {create_error}")
                    raise
            else:
                logger.error(f"Error checking S3 bucket '{bucket_name}': {e}")
                raise
    
    def upload_file(
        self,
        local_path: str,
        bucket_name: str,
        s3_key: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Upload file to S3
        
        Args:
            local_path: Local file path
            bucket_name: S3 bucket name
            s3_key: S3 object key
            metadata: Optional metadata to attach
            
        Returns:
            True if upload successful
        """
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.upload_file(
                Filename=local_path,
                Bucket=bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args
            )
            logger.info(f"Uploaded '{local_path}' to s3://{bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise
        except FileNotFoundError:
            logger.error(f"Local file not found: {local_path}")
            raise
    
    def upload_directory(
        self,
        local_dir: str,
        bucket_name: str,
        s3_prefix: str = "",
        file_extensions: Optional[List[str]] = None
    ) -> int:
        """
        Upload entire directory to S3
        
        Args:
            local_dir: Local directory path
            bucket_name: S3 bucket name
            s3_prefix: S3 key prefix
            file_extensions: Optional list of file extensions to filter (e.g., ['.pdf', '.txt'])
            
        Returns:
            Number of files uploaded
        """
        local_path = Path(local_dir)
        if not local_path.exists():
            logger.error(f"Directory not found: {local_dir}")
            raise FileNotFoundError(f"Directory not found: {local_dir}")
        
        uploaded_count = 0
        
        for file_path in local_path.rglob('*'):
            if file_path.is_file():
                # Filter by extension if specified
                if file_extensions and file_path.suffix.lower() not in file_extensions:
                    continue
                
                # Calculate relative path and S3 key
                relative_path = file_path.relative_to(local_path)
                s3_key = f"{s3_prefix}/{relative_path}".replace('\\', '/').lstrip('/')
                
                try:
                    self.upload_file(str(file_path), bucket_name, s3_key)
                    uploaded_count += 1
                except Exception as e:
                    logger.warning(f"Failed to upload {file_path}: {e}")
        
        logger.info(f"Uploaded {uploaded_count} files from '{local_dir}' to s3://{bucket_name}/{s3_prefix}")
        return uploaded_count
    
    def upload_json_data(
        self,
        data: Dict[str, Any],
        bucket_name: str,
        s3_key: str
    ) -> bool:
        """
        Upload JSON data to S3
        
        Args:
            data: Dictionary to upload as JSON
            bucket_name: S3 bucket name
            s3_key: S3 object key
            
        Returns:
            True if upload successful
        """
        try:
            json_data = json.dumps(data, indent=2)
            self.s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=json_data,
                ContentType='application/json'
            )
            logger.info(f"Uploaded JSON data to s3://{bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to upload JSON data to S3: {e}")
            raise
    
    def download_file(
        self,
        bucket_name: str,
        s3_key: str,
        local_path: str
    ) -> bool:
        """
        Download file from S3
        
        Args:
            bucket_name: S3 bucket name
            s3_key: S3 object key
            local_path: Local file path to save
            
        Returns:
            True if download successful
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            self.s3_client.download_file(
                Bucket=bucket_name,
                Key=s3_key,
                Filename=local_path
            )
            logger.info(f"Downloaded s3://{bucket_name}/{s3_key} to '{local_path}'")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to download file from S3: {e}")
            raise
    
    def list_objects(
        self,
        bucket_name: str,
        prefix: str = "",
        max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        List objects in S3 bucket
        
        Args:
            bucket_name: S3 bucket name
            prefix: S3 key prefix to filter
            max_keys: Maximum number of keys to return
            
        Returns:
            List of object metadata dictionaries
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            objects = response.get('Contents', [])
            logger.info(f"Found {len(objects)} objects in s3://{bucket_name}/{prefix}")
            return objects
            
        except ClientError as e:
            logger.error(f"Failed to list objects in S3: {e}")
            raise
    
    def delete_object(self, bucket_name: str, s3_key: str) -> bool:
        """
        Delete object from S3
        
        Args:
            bucket_name: S3 bucket name
            s3_key: S3 object key
            
        Returns:
            True if deletion successful
        """
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
            logger.info(f"Deleted s3://{bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete object from S3: {e}")
            raise
    
    def delete_objects_with_prefix(
        self,
        bucket_name: str,
        prefix: str
    ) -> int:
        """
        Delete all objects with given prefix
        
        Args:
            bucket_name: S3 bucket name
            prefix: S3 key prefix
            
        Returns:
            Number of objects deleted
        """
        try:
            objects = self.list_objects(bucket_name, prefix)
            
            if not objects:
                logger.info(f"No objects found with prefix '{prefix}'")
                return 0
            
            # Delete objects in batches
            delete_keys = [{'Key': obj['Key']} for obj in objects]
            
            response = self.s3_client.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': delete_keys}
            )
            
            deleted_count = len(response.get('Deleted', []))
            logger.info(f"Deleted {deleted_count} objects with prefix '{prefix}'")
            return deleted_count
            
        except ClientError as e:
            logger.error(f"Failed to delete objects from S3: {e}")
            raise
    
    def delete_bucket(self, bucket_name: str, force: bool = False) -> bool:
        """
        Delete S3 bucket
        
        Args:
            bucket_name: S3 bucket name
            force: If True, delete all objects before deleting bucket
            
        Returns:
            True if deletion successful
        """
        try:
            if force:
                # Delete all objects first
                logger.info(f"Deleting all objects in bucket '{bucket_name}'")
                self.delete_objects_with_prefix(bucket_name, "")
                
                # Delete all versions if versioning is enabled
                try:
                    paginator = self.s3_client.get_paginator('list_object_versions')
                    for page in paginator.paginate(Bucket=bucket_name):
                        versions = page.get('Versions', [])
                        delete_markers = page.get('DeleteMarkers', [])
                        
                        objects_to_delete = []
                        for version in versions:
                            objects_to_delete.append({
                                'Key': version['Key'],
                                'VersionId': version['VersionId']
                            })
                        for marker in delete_markers:
                            objects_to_delete.append({
                                'Key': marker['Key'],
                                'VersionId': marker['VersionId']
                            })
                        
                        if objects_to_delete:
                            self.s3_client.delete_objects(
                                Bucket=bucket_name,
                                Delete={'Objects': objects_to_delete}
                            )
                except ClientError:
                    pass  # Versioning might not be enabled
            
            # Delete bucket
            self.s3_client.delete_bucket(Bucket=bucket_name)
            logger.info(f"Deleted S3 bucket '{bucket_name}'")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                logger.info(f"S3 bucket '{bucket_name}' does not exist")
                return True
            else:
                logger.error(f"Failed to delete S3 bucket '{bucket_name}': {e}")
                raise
    
    def configure_event_notification(
        self,
        bucket_name: str,
        lambda_function_arn: str,
        prefix: str = "",
        suffix: str = "",
        events: Optional[List[str]] = None
    ) -> bool:
        """
        Configure S3 event notification to trigger Lambda
        
        Args:
            bucket_name: S3 bucket name
            lambda_function_arn: Lambda function ARN
            prefix: S3 key prefix filter
            suffix: S3 key suffix filter
            events: List of S3 events (default: ['s3:ObjectCreated:*'])
            
        Returns:
            True if configuration successful
        """
        if events is None:
            events = ['s3:ObjectCreated:*']
        
        try:
            notification_config = {
                'LambdaFunctionConfigurations': [
                    {
                        'Id': f'lambda-trigger-{prefix.replace("/", "-")}',
                        'LambdaFunctionArn': lambda_function_arn,
                        'Events': events,
                        'Filter': {
                            'Key': {
                                'FilterRules': []
                            }
                        }
                    }
                ]
            }
            
            # Add prefix filter if specified
            if prefix:
                notification_config['LambdaFunctionConfigurations'][0]['Filter']['Key']['FilterRules'].append({
                    'Name': 'prefix',
                    'Value': prefix
                })
            
            # Add suffix filter if specified
            if suffix:
                notification_config['LambdaFunctionConfigurations'][0]['Filter']['Key']['FilterRules'].append({
                    'Name': 'suffix',
                    'Value': suffix
                })
            
            self.s3_client.put_bucket_notification_configuration(
                Bucket=bucket_name,
                NotificationConfiguration=notification_config
            )
            
            logger.info(f"Configured S3 event notification for bucket '{bucket_name}'")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to configure S3 event notification: {e}")
            raise
    
    def get_object_metadata(
        self,
        bucket_name: str,
        s3_key: str
    ) -> Dict[str, Any]:
        """
        Get object metadata
        
        Args:
            bucket_name: S3 bucket name
            s3_key: S3 object key
            
        Returns:
            Object metadata dictionary
        """
        try:
            response = self.s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response.get('ContentType'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            logger.error(f"Failed to get object metadata: {e}")
            raise

