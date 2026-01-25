"""
Knowledge Base Management Module
Handles Bedrock Knowledge Base creation, data source management, and synchronization
"""

import time
import logging
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    """Manages Bedrock Knowledge Base operations"""
    
    def __init__(
        self,
        bedrock_agent_client,
        account_id: str,
        region: str
    ):
        """
        Initialize Knowledge Base Manager
        
        Args:
            bedrock_agent_client: Boto3 Bedrock Agent client
            account_id: AWS account ID
            region: AWS region
        """
        self.client = bedrock_agent_client
        self.account_id = account_id
        self.region = region
    
    def create_knowledge_base(
        self,
        kb_name: str,
        kb_description: str,
        role_arn: str,
        storage_configuration: Dict[str, Any],
        embedding_model_arn: str
    ) -> str:
        """
        Create Knowledge Base
        
        Args:
            kb_name: Name of the Knowledge Base
            kb_description: Description
            role_arn: IAM role ARN for KB execution
            storage_configuration: Storage configuration (OpenSearch)
            embedding_model_arn: ARN of the embedding model
            
        Returns:
            Knowledge Base ID
        """
        try:
            # Check if KB exists
            existing_kb = self.get_knowledge_base_by_name(kb_name)
            if existing_kb:
                kb_id = existing_kb['knowledgeBaseId']
                logger.info(f"Knowledge Base '{kb_name}' already exists: {kb_id}")
                return kb_id
            
            # Create Knowledge Base
            response = self.client.create_knowledge_base(
                name=kb_name,
                description=kb_description,
                roleArn=role_arn,
                knowledgeBaseConfiguration={
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': embedding_model_arn
                    }
                },
                storageConfiguration=storage_configuration
            )
            
            kb_id = response['knowledgeBase']['knowledgeBaseId']
            logger.info(f"Created Knowledge Base '{kb_name}': {kb_id}")
            
            # Wait for KB to be active
            self._wait_for_kb_status(kb_id, 'ACTIVE')
            
            return kb_id
            
        except ClientError as e:
            logger.error(f"Failed to create Knowledge Base: {e}")
            raise
    
    def create_data_source(
        self,
        kb_id: str,
        data_source_name: str,
        data_source_type: str,
        data_source_config: Dict[str, Any],
        vector_ingestion_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create data source for Knowledge Base
        
        Args:
            kb_id: Knowledge Base ID
            data_source_name: Name of the data source
            data_source_type: Type of data source (e.g., 'S3')
            data_source_config: Data source configuration
            vector_ingestion_config: Vector ingestion configuration
            
        Returns:
            Data source ID
        """
        try:
            # Check if data source exists
            existing_ds = self.get_data_source_by_name(kb_id, data_source_name)
            if existing_ds:
                ds_id = existing_ds['dataSourceId']
                logger.info(f"Data source '{data_source_name}' already exists: {ds_id}")
                return ds_id
            
            # Default vector ingestion config
            if vector_ingestion_config is None:
                vector_ingestion_config = {
                    'chunkingConfiguration': {
                        'chunkingStrategy': 'FIXED_SIZE',
                        'fixedSizeChunkingConfiguration': {
                            'maxTokens': 500,
                            'overlapPercentage': 10
                        }
                    }
                }
            
            # Create data source
            response = self.client.create_data_source(
                knowledgeBaseId=kb_id,
                name=data_source_name,
                dataSourceConfiguration={
                    'type': data_source_type,
                    's3Configuration': data_source_config
                },
                vectorIngestionConfiguration=vector_ingestion_config
            )
            
            ds_id = response['dataSource']['dataSourceId']
            logger.info(f"Created data source '{data_source_name}': {ds_id}")
            
            return ds_id
            
        except ClientError as e:
            logger.error(f"Failed to create data source: {e}")
            raise
    
    def start_ingestion_job(
        self,
        kb_id: str,
        data_source_id: str,
        description: str = ""
    ) -> str:
        """
        Start ingestion job for data source
        
        Args:
            kb_id: Knowledge Base ID
            data_source_id: Data source ID
            description: Job description
            
        Returns:
            Ingestion job ID
        """
        try:
            response = self.client.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id,
                description=description or "Ingestion job"
            )
            
            job_id = response['ingestionJob']['ingestionJobId']
            logger.info(f"Started ingestion job: {job_id}")
            
            return job_id
            
        except ClientError as e:
            logger.error(f"Failed to start ingestion job: {e}")
            raise
    
    def wait_for_ingestion_job(
        self,
        kb_id: str,
        data_source_id: str,
        job_id: str,
        max_wait_time: int = 600,
        check_interval: int = 10
    ) -> str:
        """
        Wait for ingestion job to complete
        
        Args:
            kb_id: Knowledge Base ID
            data_source_id: Data source ID
            job_id: Ingestion job ID
            max_wait_time: Maximum wait time in seconds
            check_interval: Check interval in seconds
            
        Returns:
            Final job status
        """
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            try:
                response = self.client.get_ingestion_job(
                    knowledgeBaseId=kb_id,
                    dataSourceId=data_source_id,
                    ingestionJobId=job_id
                )
                
                status = response['ingestionJob']['status']
                
                if status == 'COMPLETE':
                    logger.info(f"Ingestion job {job_id} completed successfully")
                    return status
                elif status == 'FAILED':
                    failure_reasons = response['ingestionJob'].get('failureReasons', [])
                    logger.error(f"Ingestion job failed: {failure_reasons}")
                    raise Exception(f"Ingestion job failed: {failure_reasons}")
                
                logger.info(f"Ingestion job status: {status}. Waiting...")
                
            except ClientError as e:
                logger.error(f"Error checking ingestion job status: {e}")
                raise
            
            time.sleep(check_interval)
            elapsed_time += check_interval
        
        raise TimeoutError(f"Ingestion job did not complete within {max_wait_time} seconds")
    
    def sync_data_source(
        self,
        kb_id: str,
        data_source_id: str,
        wait_for_completion: bool = True
    ) -> str:
        """
        Synchronize data source (start ingestion and optionally wait)
        
        Args:
            kb_id: Knowledge Base ID
            data_source_id: Data source ID
            wait_for_completion: Wait for job to complete
            
        Returns:
            Ingestion job ID
        """
        job_id = self.start_ingestion_job(kb_id, data_source_id)
        
        if wait_for_completion:
            self.wait_for_ingestion_job(kb_id, data_source_id, job_id)
        
        return job_id
    
    def get_knowledge_base_by_name(self, kb_name: str) -> Optional[Dict[str, Any]]:
        """
        Get Knowledge Base by name
        
        Args:
            kb_name: Name of the Knowledge Base
            
        Returns:
            Knowledge Base details or None if not found
        """
        try:
            response = self.client.list_knowledge_bases(maxResults=100)
            
            for kb in response.get('knowledgeBaseSummaries', []):
                if kb['name'] == kb_name:
                    # Get full details
                    kb_response = self.client.get_knowledge_base(
                        knowledgeBaseId=kb['knowledgeBaseId']
                    )
                    return kb_response['knowledgeBase']
            
            return None
            
        except ClientError as e:
            logger.error(f"Failed to get Knowledge Base by name: {e}")
            return None
    
    def get_data_source_by_name(
        self,
        kb_id: str,
        data_source_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get data source by name
        
        Args:
            kb_id: Knowledge Base ID
            data_source_name: Name of the data source
            
        Returns:
            Data source details or None if not found
        """
        try:
            response = self.client.list_data_sources(
                knowledgeBaseId=kb_id,
                maxResults=100
            )
            
            for ds in response.get('dataSourceSummaries', []):
                if ds['name'] == data_source_name:
                    # Get full details
                    ds_response = self.client.get_data_source(
                        knowledgeBaseId=kb_id,
                        dataSourceId=ds['dataSourceId']
                    )
                    return ds_response['dataSource']
            
            return None
            
        except ClientError as e:
            logger.error(f"Failed to get data source by name: {e}")
            return None
    
    def delete_knowledge_base(self, kb_id: str) -> bool:
        """
        Delete Knowledge Base
        
        Args:
            kb_id: Knowledge Base ID
            
        Returns:
            True if deletion successful
        """
        try:
            # Delete all data sources first
            response = self.client.list_data_sources(
                knowledgeBaseId=kb_id,
                maxResults=100
            )
            
            for ds in response.get('dataSourceSummaries', []):
                self.delete_data_source(kb_id, ds['dataSourceId'])
            
            # Delete Knowledge Base
            self.client.delete_knowledge_base(knowledgeBaseId=kb_id)
            logger.info(f"Deleted Knowledge Base: {kb_id}")
            
            return True
            
        except self.client.exceptions.ResourceNotFoundException:
            logger.info(f"Knowledge Base {kb_id} does not exist")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete Knowledge Base: {e}")
            raise
    
    def delete_data_source(self, kb_id: str, data_source_id: str) -> bool:
        """
        Delete data source
        
        Args:
            kb_id: Knowledge Base ID
            data_source_id: Data source ID
            
        Returns:
            True if deletion successful
        """
        try:
            self.client.delete_data_source(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id
            )
            logger.info(f"Deleted data source: {data_source_id}")
            return True
            
        except self.client.exceptions.ResourceNotFoundException:
            logger.info(f"Data source {data_source_id} does not exist")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete data source: {e}")
            raise
    
    def retrieve_from_kb(
        self,
        kb_id: str,
        query: str,
        number_of_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents from Knowledge Base
        
        Args:
            kb_id: Knowledge Base ID
            query: Query text
            number_of_results: Number of results to return
            
        Returns:
            List of retrieved documents
        """
        try:
            # Use bedrock-agent-runtime client for retrieval
            from boto3 import client as boto3_client
            runtime_client = boto3_client('bedrock-agent-runtime', region_name=self.region)
            
            response = runtime_client.retrieve(
                knowledgeBaseId=kb_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': number_of_results
                    }
                }
            )
            
            results = []
            for result in response.get('retrievalResults', []):
                results.append({
                    'content': result['content']['text'],
                    'score': result.get('score', 0),
                    'location': result.get('location', {}),
                    'metadata': result.get('metadata', {})
                })
            
            logger.info(f"Retrieved {len(results)} documents from KB")
            return results
            
        except ClientError as e:
            logger.error(f"Failed to retrieve from Knowledge Base: {e}")
            raise
    
    def _wait_for_kb_status(
        self,
        kb_id: str,
        target_status: str,
        max_wait_time: int = 300,
        check_interval: int = 5
    ):
        """
        Wait for Knowledge Base to reach target status
        
        Args:
            kb_id: Knowledge Base ID
            target_status: Target status to wait for
            max_wait_time: Maximum wait time in seconds
            check_interval: Check interval in seconds
        """
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            try:
                response = self.client.get_knowledge_base(knowledgeBaseId=kb_id)
                status = response['knowledgeBase']['status']
                
                if status == target_status:
                    return
                elif status == 'FAILED':
                    raise Exception(f"Knowledge Base entered FAILED state")
                
                logger.info(f"Knowledge Base status: {status}. Waiting for {target_status}...")
                
            except ClientError as e:
                logger.error(f"Error checking Knowledge Base status: {e}")
                raise
            
            time.sleep(check_interval)
            elapsed_time += check_interval
        
        raise TimeoutError(f"Knowledge Base did not reach {target_status} within {max_wait_time} seconds")
    
    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """
        List all Knowledge Bases
        
        Returns:
            List of Knowledge Base summaries
        """
        try:
            response = self.client.list_knowledge_bases(maxResults=100)
            kbs = response.get('knowledgeBaseSummaries', [])
            logger.info(f"Found {len(kbs)} Knowledge Bases")
            return kbs
            
        except ClientError as e:
            logger.error(f"Failed to list Knowledge Bases: {e}")
            raise
    
    def get_ingestion_job_status(
        self,
        kb_id: str,
        data_source_id: str,
        job_id: str
    ) -> Dict[str, Any]:
        """
        Get ingestion job status
        
        Args:
            kb_id: Knowledge Base ID
            data_source_id: Data source ID
            job_id: Ingestion job ID
            
        Returns:
            Job status information
        """
        try:
            response = self.client.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id,
                ingestionJobId=job_id
            )
            
            job = response['ingestionJob']
            return {
                'status': job['status'],
                'started_at': job.get('startedAt'),
                'updated_at': job.get('updatedAt'),
                'statistics': job.get('statistics', {}),
                'failure_reasons': job.get('failureReasons', [])
            }
            
        except ClientError as e:
            logger.error(f"Failed to get ingestion job status: {e}")
            raise


