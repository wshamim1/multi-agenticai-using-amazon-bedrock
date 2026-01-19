"""
OpenSearch Serverless Management Module
Handles OpenSearch Serverless collection and index operations for Knowledge Base
"""

import json
import time
import logging
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3

logger = logging.getLogger(__name__)


class OpenSearchManager:
    """Manages OpenSearch Serverless operations"""
    
    def __init__(
        self,
        opensearch_client,
        account_id: str,
        region: str
    ):
        """
        Initialize OpenSearch Manager
        
        Args:
            opensearch_client: Boto3 OpenSearch Serverless client
            account_id: AWS account ID
            region: AWS region
        """
        self.client = opensearch_client
        self.account_id = account_id
        self.region = region
    
    def create_encryption_policy(
        self,
        policy_name: str,
        collection_name: str
    ) -> str:
        """
        Create encryption policy for OpenSearch collection
        
        Args:
            policy_name: Name of the encryption policy
            collection_name: Name of the collection
            
        Returns:
            Policy name
        """
        policy = {
            "Rules": [
                {
                    "Resource": [f"collection/{collection_name}"],
                    "ResourceType": "collection"
                }
            ],
            "AWSOwnedKey": True
        }
        
        try:
            # Check if policy exists
            try:
                self.client.get_security_policy(
                    name=policy_name,
                    type='encryption'
                )
                logger.info(f"Encryption policy '{policy_name}' already exists")
                return policy_name
            except self.client.exceptions.ResourceNotFoundException:
                pass
            
            # Create policy
            response = self.client.create_security_policy(
                name=policy_name,
                type='encryption',
                policy=json.dumps(policy)
            )
            logger.info(f"Created encryption policy '{policy_name}'")
            return response['securityPolicyDetail']['name']
            
        except ClientError as e:
            # If conflict, policy already exists for this collection
            if e.response['Error']['Code'] == 'ConflictException':
                logger.warning(f"Encryption policy conflict for collection '{collection_name}' - using existing policy")
                return policy_name
            logger.error(f"Failed to create encryption policy: {e}")
            raise
    
    def create_network_policy(
        self,
        policy_name: str,
        collection_name: str,
        public_access: bool = True
    ) -> str:
        """
        Create network policy for OpenSearch collection
        
        Args:
            policy_name: Name of the network policy
            collection_name: Name of the collection
            public_access: Allow public access
            
        Returns:
            Policy name
        """
        policy = [
            {
                "Rules": [
                    {
                        "Resource": [f"collection/{collection_name}"],
                        "ResourceType": "collection"
                    }
                ],
                "AllowFromPublic": public_access
            }
        ]
        
        try:
            # Check if policy exists
            try:
                self.client.get_security_policy(
                    name=policy_name,
                    type='network'
                )
                logger.info(f"Network policy '{policy_name}' already exists")
                return policy_name
            except self.client.exceptions.ResourceNotFoundException:
                pass
            
            # Create policy
            response = self.client.create_security_policy(
                name=policy_name,
                type='network',
                policy=json.dumps(policy)
            )
            logger.info(f"Created network policy '{policy_name}'")
            return response['securityPolicyDetail']['name']
            
        except ClientError as e:
            # If conflict, policy already exists for this collection
            if e.response['Error']['Code'] == 'ConflictException':
                logger.warning(f"Network policy conflict for collection '{collection_name}' - using existing policy")
                return policy_name
            logger.error(f"Failed to create network policy: {e}")
            raise
    
    def create_data_access_policy(
        self,
        policy_name: str,
        collection_name: str,
        principal_arn: str
    ) -> str:
        """
        Create data access policy for OpenSearch collection
        
        Args:
            policy_name: Name of the data access policy
            collection_name: Name of the collection
            principal_arn: ARN of the principal (IAM role)
            
        Returns:
            Policy name
        """
        # Get current user/role ARN
        try:
            sts = boto3.client('sts')
            caller_identity = sts.get_caller_identity()
            current_user_arn = caller_identity['Arn']
            logger.info(f"Current user ARN: {current_user_arn}")
        except Exception as e:
            logger.warning(f"Could not get current user ARN: {e}")
            current_user_arn = None
        
        # Include IAM role, root user, and current user for broader access
        principals = [principal_arn]
        
        # Add root user
        principals.append(f"arn:aws:iam::{self.account_id}:root")
        
        # Add current user if different from root
        if current_user_arn and current_user_arn not in principals:
            principals.append(current_user_arn)
            logger.info(f"Added current user to data access policy: {current_user_arn}")
        
        policy = [
            {
                "Rules": [
                    {
                        "Resource": [f"collection/{collection_name}"],
                        "Permission": [
                            "aoss:CreateCollectionItems",
                            "aoss:DeleteCollectionItems",
                            "aoss:UpdateCollectionItems",
                            "aoss:DescribeCollectionItems"
                        ],
                        "ResourceType": "collection"
                    },
                    {
                        "Resource": [f"index/{collection_name}/*"],
                        "Permission": [
                            "aoss:CreateIndex",
                            "aoss:DeleteIndex",
                            "aoss:UpdateIndex",
                            "aoss:DescribeIndex",
                            "aoss:ReadDocument",
                            "aoss:WriteDocument"
                        ],
                        "ResourceType": "index"
                    }
                ],
                "Principal": principals,
                "Description": f"Data access policy for {collection_name}"
            }
        ]
        
        try:
            # Check if policy exists
            try:
                self.client.get_access_policy(
                    name=policy_name,
                    type='data'
                )
                logger.info(f"Data access policy '{policy_name}' already exists")
                return policy_name
            except self.client.exceptions.ResourceNotFoundException:
                pass
            
            # Create policy
            response = self.client.create_access_policy(
                name=policy_name,
                type='data',
                policy=json.dumps(policy)
            )
            logger.info(f"Created data access policy '{policy_name}'")
            return response['accessPolicyDetail']['name']
            
        except ClientError as e:
            # If conflict, policy already exists for this collection
            if e.response['Error']['Code'] == 'ConflictException':
                logger.warning(f"Data access policy conflict for collection '{collection_name}' - using existing policy")
                return policy_name
            logger.error(f"Failed to create data access policy: {e}")
            raise
    
    def create_collection(
        self,
        collection_name: str,
        description: str = ""
    ) -> Dict[str, str]:
        """
        Create OpenSearch Serverless collection
        
        Args:
            collection_name: Name of the collection
            description: Collection description
            
        Returns:
            Dictionary with collection ID, ARN, and endpoint
        """
        try:
            # Check if collection exists
            try:
                response = self.client.batch_get_collection(
                    names=[collection_name]
                )
                if response['collectionDetails']:
                    collection = response['collectionDetails'][0]
                    logger.info(f"Collection '{collection_name}' already exists")
                    return {
                        'id': collection['id'],
                        'arn': collection['arn'],
                        'endpoint': collection['collectionEndpoint']
                    }
            except (ClientError, KeyError):
                pass
            
            # Create collection
            response = self.client.create_collection(
                name=collection_name,
                type='VECTORSEARCH',
                description=description or f"Vector search collection for {collection_name}"
            )
            
            collection_id = response['createCollectionDetail']['id']
            collection_arn = response['createCollectionDetail']['arn']
            
            logger.info(f"Creating collection '{collection_name}' (ID: {collection_id})")
            
            # Wait for collection to be active
            self._wait_for_collection_active(collection_name)
            
            # Get collection endpoint
            response = self.client.batch_get_collection(names=[collection_name])
            endpoint = response['collectionDetails'][0]['collectionEndpoint']
            
            logger.info(f"Collection '{collection_name}' is active. Endpoint: {endpoint}")
            
            return {
                'id': collection_id,
                'arn': collection_arn,
                'endpoint': endpoint
            }
            
        except ClientError as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    def _wait_for_collection_active(
        self,
        collection_name: str,
        max_wait_time: int = 600,
        check_interval: int = 10
    ):
        """
        Wait for collection to become active
        
        Args:
            collection_name: Name of the collection
            max_wait_time: Maximum wait time in seconds
            check_interval: Check interval in seconds
        """
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            try:
                response = self.client.batch_get_collection(names=[collection_name])
                if response['collectionDetails']:
                    status = response['collectionDetails'][0]['status']
                    if status == 'ACTIVE':
                        return
                    elif status == 'FAILED':
                        raise Exception(f"Collection creation failed")
                    
                    logger.info(f"Collection status: {status}. Waiting...")
            except ClientError:
                pass
            
            time.sleep(check_interval)
            elapsed_time += check_interval
        
        raise TimeoutError(f"Collection did not become active within {max_wait_time} seconds")
    
    def create_vector_index(
        self,
        collection_endpoint: str,
        index_name: str,
        vector_field: str = "vector",
        text_field: str = "text",
        metadata_field: str = "metadata",
        vector_dimension: int = 1536
    ) -> bool:
        """
        Create vector index in OpenSearch collection
        
        Args:
            collection_endpoint: Collection endpoint URL
            index_name: Name of the index
            vector_field: Name of the vector field
            text_field: Name of the text field
            metadata_field: Name of the metadata field
            vector_dimension: Dimension of the vector embeddings
            
        Returns:
            True if index created successfully
        """
        try:
            # Get AWS credentials for authentication
            credentials = boto3.Session().get_credentials()
            auth = AWSV4SignerAuth(credentials, self.region, 'aoss')
            
            # Create OpenSearch client
            host = collection_endpoint.replace('https://', '')
            os_client = OpenSearch(
                hosts=[{'host': host, 'port': 443}],
                http_auth=auth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection,
                timeout=300
            )
            
            # Check if index exists
            if os_client.indices.exists(index=index_name):
                logger.info(f"Index '{index_name}' already exists")
                return True
            
            # Define index mapping
            index_body = {
                "settings": {
                    "index": {
                        "knn": True,
                        "knn.algo_param.ef_search": 512
                    }
                },
                "mappings": {
                    "properties": {
                        vector_field: {
                            "type": "knn_vector",
                            "dimension": vector_dimension,
                            "method": {
                                "name": "hnsw",
                                "engine": "faiss",
                                "parameters": {
                                    "ef_construction": 512,
                                    "m": 16
                                },
                                "space_type": "l2"
                            }
                        },
                        text_field: {
                            "type": "text"
                        },
                        metadata_field: {
                            "type": "text",
                            "index": False
                        }
                    }
                }
            }
            
            # Create index
            os_client.indices.create(index=index_name, body=index_body)
            logger.info(f"Created vector index '{index_name}'")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create vector index: {e}")
            raise
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete OpenSearch collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            True if deletion successful
        """
        try:
            # First, get the collection ID from the name
            response = self.client.batch_get_collection(names=[collection_name])
            
            if not response.get('collectionDetails'):
                logger.info(f"Collection '{collection_name}' does not exist")
                return True
            
            collection_id = response['collectionDetails'][0]['id']
            
            # Delete using collection ID (required parameter)
            self.client.delete_collection(id=collection_id)
            logger.info(f"Deleted collection '{collection_name}' (ID: {collection_id})")
            return True
            
        except self.client.exceptions.ResourceNotFoundException:
            logger.info(f"Collection '{collection_name}' does not exist")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete collection: {e}")
            raise
    
    def delete_security_policy(
        self,
        policy_name: str,
        policy_type: str
    ) -> bool:
        """
        Delete security policy
        
        Args:
            policy_name: Name of the policy
            policy_type: Type of policy ('encryption' or 'network')
            
        Returns:
            True if deletion successful
        """
        try:
            self.client.delete_security_policy(
                name=policy_name,
                type=policy_type
            )
            logger.info(f"Deleted {policy_type} policy '{policy_name}'")
            return True
            
        except self.client.exceptions.ResourceNotFoundException:
            logger.info(f"Policy '{policy_name}' does not exist")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete security policy: {e}")
            raise
    
    def delete_access_policy(self, policy_name: str) -> bool:
        """
        Delete data access policy
        
        Args:
            policy_name: Name of the policy
            
        Returns:
            True if deletion successful
        """
        try:
            self.client.delete_access_policy(
                name=policy_name,
                type='data'
            )
            logger.info(f"Deleted data access policy '{policy_name}'")
            return True
            
        except self.client.exceptions.ResourceNotFoundException:
            logger.info(f"Policy '{policy_name}' does not exist")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete access policy: {e}")
            raise
    
    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """
        Get collection information
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection information or None if not found
        """
        try:
            response = self.client.batch_get_collection(names=[collection_name])
            if response['collectionDetails']:
                collection = response['collectionDetails'][0]
                return {
                    'id': collection['id'],
                    'name': collection['name'],
                    'arn': collection['arn'],
                    'status': collection['status'],
                    'endpoint': collection.get('collectionEndpoint'),
                    'created_date': collection.get('createdDate')
                }
            return None
            
        except ClientError as e:
            logger.error(f"Failed to get collection info: {e}")
            return None

# Made with Bob
