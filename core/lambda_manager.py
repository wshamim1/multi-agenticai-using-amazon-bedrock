"""
Lambda Function Management Module
Handles creation, deployment, and management of Lambda functions
"""

import os
import json
import time
import zipfile
import logging
from io import BytesIO
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class LambdaManager:
    """Manages Lambda function operations"""
    
    def __init__(
        self,
        lambda_client,
        iam_client,
        account_id: str,
        region: str
    ):
        """
        Initialize Lambda Manager
        
        Args:
            lambda_client: Boto3 Lambda client
            iam_client: Boto3 IAM client
            account_id: AWS account ID
            region: AWS region
        """
        self.lambda_client = lambda_client
        self.iam_client = iam_client
        self.account_id = account_id
        self.region = region
    
    def create_deployment_package(
        self,
        handler_code: str,
        handler_filename: str = "lambda_function.py",
        additional_files: Optional[Dict[str, str]] = None
    ) -> bytes:
        """
        Create Lambda deployment package (ZIP file)
        
        Args:
            handler_code: Lambda handler code
            handler_filename: Name of the handler file
            additional_files: Dictionary of {filename: content} for additional files
            
        Returns:
            ZIP file bytes
        """
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add handler file
            zip_file.writestr(handler_filename, handler_code)
            
            # Add additional files if provided
            if additional_files:
                for filename, content in additional_files.items():
                    zip_file.writestr(filename, content)
        
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    def create_function(
        self,
        function_name: str,
        handler_code: str,
        role_arn: str,
        handler: str = "lambda_function.lambda_handler",
        runtime: str = "python3.11",
        timeout: int = 300,
        memory_size: int = 512,
        environment_vars: Optional[Dict[str, str]] = None,
        additional_files: Optional[Dict[str, str]] = None,
        layers: Optional[List[str]] = None
    ) -> str:
        """
        Create or update Lambda function
        
        Args:
            function_name: Name of the Lambda function
            handler_code: Lambda handler code
            role_arn: IAM role ARN for Lambda execution
            handler: Handler method (default: lambda_function.lambda_handler)
            runtime: Python runtime version
            timeout: Function timeout in seconds
            memory_size: Memory allocation in MB
            environment_vars: Environment variables
            additional_files: Additional files to include in deployment package
            layers: List of Lambda layer ARNs
            
        Returns:
            Lambda function ARN
        """
        try:
            # Check if function exists
            response = self.lambda_client.get_function(FunctionName=function_name)
            function_arn = response['Configuration']['FunctionArn']
            logger.info(f"Lambda function '{function_name}' already exists, updating...")
            
            # Update function code
            deployment_package = self.create_deployment_package(
                handler_code,
                additional_files=additional_files
            )
            
            self.lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=deployment_package
            )
            
            # Wait for update to complete
            waiter = self.lambda_client.get_waiter('function_updated')
            waiter.wait(FunctionName=function_name)
            
            # Update function configuration
            update_config = {
                'FunctionName': function_name,
                'Role': role_arn,
                'Handler': handler,
                'Runtime': runtime,
                'Timeout': timeout,
                'MemorySize': memory_size
            }
            
            if environment_vars:
                update_config['Environment'] = {'Variables': environment_vars}
            
            if layers:
                update_config['Layers'] = layers
            
            self.lambda_client.update_function_configuration(**update_config)
            
            logger.info(f"Updated Lambda function '{function_name}': {function_arn}")
            return function_arn
            
        except self.lambda_client.exceptions.ResourceNotFoundException:
            # Create new function
            try:
                deployment_package = self.create_deployment_package(
                    handler_code,
                    additional_files=additional_files
                )
                
                create_config = {
                    'FunctionName': function_name,
                    'Runtime': runtime,
                    'Role': role_arn,
                    'Handler': handler,
                    'Code': {'ZipFile': deployment_package},
                    'Timeout': timeout,
                    'MemorySize': memory_size,
                    'Publish': True
                }
                
                if environment_vars:
                    create_config['Environment'] = {'Variables': environment_vars}
                
                if layers:
                    create_config['Layers'] = layers
                
                response = self.lambda_client.create_function(**create_config)
                function_arn = response['FunctionArn']
                
                logger.info(f"Created Lambda function '{function_name}': {function_arn}")
                
                # Wait for function to be active
                time.sleep(5)
                return function_arn
                
            except ClientError as e:
                logger.error(f"Failed to create Lambda function '{function_name}': {e}")
                raise
    
    def add_bedrock_invoke_permission(self, function_name: str) -> bool:
        """
        Add permission for Bedrock to invoke Lambda function
        
        Args:
            function_name: Name of the Lambda function
            
        Returns:
            True if permission added successfully
        """
        try:
            statement_id = f"bedrock-invoke-{function_name}"
            
            # Remove existing permission if it exists
            try:
                self.lambda_client.remove_permission(
                    FunctionName=function_name,
                    StatementId=statement_id
                )
                logger.info(f"Removed existing Bedrock invoke permission for '{function_name}'")
            except self.lambda_client.exceptions.ResourceNotFoundException:
                pass
            
            # Add new permission
            self.lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=statement_id,
                Action='lambda:InvokeFunction',
                Principal='bedrock.amazonaws.com',
                SourceAccount=self.account_id,
                SourceArn=f"arn:aws:bedrock:{self.region}:{self.account_id}:agent/*"
            )
            
            logger.info(f"Added Bedrock invoke permission for Lambda function '{function_name}'")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to add Bedrock invoke permission: {e}")
            raise
    
    def add_s3_invoke_permission(
        self,
        function_name: str,
        bucket_name: str
    ) -> bool:
        """
        Add permission for S3 to invoke Lambda function
        
        Args:
            function_name: Name of the Lambda function
            bucket_name: S3 bucket name
            
        Returns:
            True if permission added successfully
        """
        try:
            statement_id = f"s3-invoke-{bucket_name}"
            
            # Remove existing permission if it exists
            try:
                self.lambda_client.remove_permission(
                    FunctionName=function_name,
                    StatementId=statement_id
                )
                logger.info(f"Removed existing S3 invoke permission for '{function_name}'")
            except self.lambda_client.exceptions.ResourceNotFoundException:
                pass
            
            # Add new permission
            self.lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=statement_id,
                Action='lambda:InvokeFunction',
                Principal='s3.amazonaws.com',
                SourceAccount=self.account_id,
                SourceArn=f"arn:aws:s3:::{bucket_name}"
            )
            
            logger.info(f"Added S3 invoke permission for Lambda function '{function_name}'")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to add S3 invoke permission: {e}")
            raise
    
    def invoke_function(
        self,
        function_name: str,
        payload: Dict[str, Any],
        invocation_type: str = "RequestResponse"
    ) -> Dict[str, Any]:
        """
        Invoke Lambda function
        
        Args:
            function_name: Name of the Lambda function
            payload: Input payload
            invocation_type: 'RequestResponse' or 'Event'
            
        Returns:
            Response from Lambda function
        """
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(payload)
            )
            
            if invocation_type == "RequestResponse":
                result = json.loads(response['Payload'].read())
                logger.info(f"Invoked Lambda function '{function_name}' successfully")
                return result
            else:
                logger.info(f"Triggered Lambda function '{function_name}' asynchronously")
                return {"StatusCode": response['StatusCode']}
                
        except ClientError as e:
            logger.error(f"Failed to invoke Lambda function '{function_name}': {e}")
            raise
    
    def delete_function(self, function_name: str) -> bool:
        """
        Delete Lambda function
        
        Args:
            function_name: Name of the Lambda function
            
        Returns:
            True if deletion successful
        """
        try:
            self.lambda_client.delete_function(FunctionName=function_name)
            logger.info(f"Deleted Lambda function '{function_name}'")
            return True
            
        except self.lambda_client.exceptions.ResourceNotFoundException:
            logger.info(f"Lambda function '{function_name}' does not exist")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete Lambda function '{function_name}': {e}")
            raise
    
    def get_function_arn(self, function_name: str) -> Optional[str]:
        """
        Get Lambda function ARN
        
        Args:
            function_name: Name of the Lambda function
            
        Returns:
            Function ARN or None if not found
        """
        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            return response['Configuration']['FunctionArn']
        except self.lambda_client.exceptions.ResourceNotFoundException:
            return None
        except ClientError as e:
            logger.error(f"Failed to get Lambda function ARN: {e}")
            raise
    
    def update_environment_variables(
        self,
        function_name: str,
        environment_vars: Dict[str, str]
    ) -> bool:
        """
        Update Lambda function environment variables
        
        Args:
            function_name: Name of the Lambda function
            environment_vars: Environment variables to set
            
        Returns:
            True if update successful
        """
        try:
            self.lambda_client.update_function_configuration(
                FunctionName=function_name,
                Environment={'Variables': environment_vars}
            )
            logger.info(f"Updated environment variables for Lambda function '{function_name}'")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to update environment variables: {e}")
            raise
    
    def add_lambda_policy_to_role(
        self,
        role_name: str,
        policy_statements: List[Dict[str, Any]]
    ) -> str:
        """
        Add inline policy to Lambda execution role
        
        Args:
            role_name: IAM role name
            policy_statements: List of policy statements
            
        Returns:
            Policy name
        """
        policy_name = f"{role_name}-inline-policy"
        
        policy_document = {
            "Version": "2012-10-17",
            "Statement": policy_statements
        }
        
        try:
            self.iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            logger.info(f"Added inline policy '{policy_name}' to role '{role_name}'")
            return policy_name
            
        except ClientError as e:
            logger.error(f"Failed to add inline policy to role: {e}")
            raise
    
    def create_kb_sync_lambda(
        self,
        function_name: str,
        role_arn: str,
        kb_id: str,
        data_source_id: str
    ) -> str:
        """
        Create Lambda function for Knowledge Base synchronization
        
        Args:
            function_name: Name of the Lambda function
            role_arn: IAM role ARN
            kb_id: Knowledge Base ID
            data_source_id: Data source ID
            
        Returns:
            Lambda function ARN
        """
        handler_code = f'''
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock_agent_client = boto3.client('bedrock-agent')

def lambda_handler(event, context):
    """
    Triggered by S3 events to sync Knowledge Base data source
    """
    try:
        logger.info(f"Received event: {{json.dumps(event)}}")
        
        # Start ingestion job
        response = bedrock_agent_client.start_ingestion_job(
            knowledgeBaseId='{kb_id}',
            dataSourceId='{data_source_id}'
        )
        
        ingestion_job_id = response['ingestionJob']['ingestionJobId']
        logger.info(f"Started ingestion job: {{ingestion_job_id}}")
        
        return {{
            'statusCode': 200,
            'body': json.dumps({{
                'message': 'Ingestion job started successfully',
                'ingestionJobId': ingestion_job_id
            }})
        }}
        
    except Exception as e:
        logger.error(f"Error starting ingestion job: {{str(e)}}")
        return {{
            'statusCode': 500,
            'body': json.dumps({{'error': str(e)}})
        }}
'''
        
        return self.create_function(
            function_name=function_name,
            handler_code=handler_code,
            role_arn=role_arn,
            timeout=300,
            memory_size=256
        )
    
    def list_functions(self, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List Lambda functions
        
        Args:
            prefix: Optional prefix to filter function names
            
        Returns:
            List of function configurations
        """
        try:
            functions = []
            paginator = self.lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for func in page['Functions']:
                    if prefix is None or func['FunctionName'].startswith(prefix):
                        functions.append({
                            'name': func['FunctionName'],
                            'arn': func['FunctionArn'],
                            'runtime': func['Runtime'],
                            'handler': func['Handler'],
                            'last_modified': func['LastModified']
                        })
            
            logger.info(f"Found {len(functions)} Lambda functions")
            return functions
            
        except ClientError as e:
            logger.error(f"Failed to list Lambda functions: {e}")
            raise

