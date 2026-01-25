"""
Multi-Agent Orchestrator
Coordinates the setup and management of the entire ETL multi-agent system
"""

import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from config import config
from core.iam_manager import IAMManager
from core.storage_manager import StorageManager
from core.lambda_manager import LambdaManager
from core.opensearch_manager import OpenSearchManager
from core.knowledge_base_manager import KnowledgeBaseManager
from core.agent_manager import AgentManager

logger = logging.getLogger(__name__)


@dataclass
class CollaboratorConfig:
    """Configuration for a collaborator agent"""
    name: str
    instruction: str
    description: str
    action_group_name: str
    action_group_description: str
    lambda_function_name: str
    lambda_handler_code: str
    functions: List[Dict[str, Any]]
    enabled: bool = True
    utils_code: Optional[str] = None


class MultiAgentOrchestrator:
    """Orchestrates the multi-agent ETL system setup"""
    
    def __init__(self):
        """Initialize orchestrator with all managers"""
        self.config = config
        
        # Initialize managers
        self.iam_mgr = IAMManager(
            config.aws.iam_client,
            config.aws.account_id,
            config.aws.region
        )
        
        self.storage_mgr = StorageManager(
            config.aws.s3_client,
            config.aws.region
        )
        
        self.lambda_mgr = LambdaManager(
            config.aws.lambda_client,
            config.aws.iam_client,
            config.aws.account_id,
            config.aws.region
        )
        
        self.opensearch_mgr = OpenSearchManager(
            config.aws.opensearch_client,
            config.aws.account_id,
            config.aws.region
        )
        
        self.kb_mgr = KnowledgeBaseManager(
            config.aws.bedrock_agent_client,
            config.aws.account_id,
            config.aws.region
        )
        
        self.agent_mgr = AgentManager(
            config.aws.bedrock_agent_client,
            config.aws.bedrock_agent_runtime_client,
            config.aws.account_id,
            config.aws.region
        )
        
        logger.info("Multi-Agent Orchestrator initialized")
    
    def setup_iam_roles(self) -> Dict[str, str]:
        """
        Setup all required IAM roles and policies
        
        Returns:
            Dictionary with role ARNs
        """
        logger.info("=" * 60)
        logger.info("Setting up IAM roles and policies...")
        logger.info("=" * 60)
        
        # Lambda execution role
        lambda_role_arn = self.iam_mgr.create_lambda_execution_role(
            self.config.agent.lambda_role_name
        )
        
        # Bedrock agent role
        agent_role_name = self.config.agent.get_agent_role_name(self.config.aws.suffix)
        agent_role_arn = self.iam_mgr.create_bedrock_agent_role(
            agent_role_name,
            self.config.agent.agent_name
        )
        
        # Bedrock agent policy
        policy_name = self.config.agent.get_bedrock_policy_name(self.config.aws.suffix)
        policy_arn = self.iam_mgr.create_bedrock_agent_policy(
            policy_name,
            self.config.agent.foundation_model
        )
        self.iam_mgr.attach_policy_to_role(agent_role_name, policy_arn)
        
        # Knowledge Base execution role
        kb_role_arn = self.iam_mgr.create_kb_execution_role(
            self.config.kb.kb_role_name
        )
        
        logger.info(f"✅ IAM roles created successfully")
        
        return {
            'lambda_role_arn': lambda_role_arn,
            'agent_role_arn': agent_role_arn,
            'kb_role_arn': kb_role_arn
        }
    
    def setup_storage(self) -> str:
        """
        Setup S3 bucket for data storage
        
        Returns:
            Bucket name
        """
        logger.info("=" * 60)
        logger.info("Setting up S3 storage...")
        logger.info("=" * 60)
        
        bucket_name = self.config.storage.bucket_name
        self.storage_mgr.create_bucket(bucket_name)
        
        logger.info(f"✅ S3 bucket '{bucket_name}' ready")
        return bucket_name
    
    def setup_opensearch(self, kb_role_arn: str) -> Dict[str, str]:
        """
        Setup OpenSearch Serverless collection and index
        
        Args:
            kb_role_arn: Knowledge Base IAM role ARN
            
        Returns:
            Dictionary with collection info
        """
        logger.info("=" * 60)
        logger.info("Setting up OpenSearch Serverless...")
        logger.info("=" * 60)
        
        collection_name = self.config.kb.collection_name
        
        # Create security policies with shortened names (max 32 chars)
        # Use timestamp suffix to ensure uniqueness
        import time
        suffix = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
        
        self.opensearch_mgr.create_encryption_policy(
            f"kb-encrypt-{suffix}",
            collection_name
        )
        
        self.opensearch_mgr.create_network_policy(
            f"kb-network-{suffix}",
            collection_name
        )
        
        self.opensearch_mgr.create_data_access_policy(
            f"kb-access-{suffix}",
            collection_name,
            kb_role_arn
        )
        
        # Create collection
        collection_info = self.opensearch_mgr.create_collection(
            collection_name,
            f"Vector search collection for {self.config.kb.kb_name}"
        )
        
        # Create vector index
        self.opensearch_mgr.create_vector_index(
            collection_info['endpoint'],
            self.config.kb.vector_index_name,
            self.config.kb.vector_field,
            self.config.kb.text_field,
            self.config.kb.metadata_field
        )
        
        logger.info(f"✅ OpenSearch collection and index ready")
        return collection_info
    
    def setup_knowledge_base(
        self,
        kb_role_arn: str,
        collection_arn: str,
        bucket_name: str
    ) -> str:
        """
        Setup Knowledge Base with data source
        
        Args:
            kb_role_arn: KB IAM role ARN
            collection_arn: OpenSearch collection ARN
            bucket_name: S3 bucket name
            
        Returns:
            Knowledge Base ID
        """
        logger.info("=" * 60)
        logger.info("Setting up Knowledge Base...")
        logger.info("=" * 60)
        
        # Create KB policies
        bedrock_policy_arn = self.iam_mgr.create_kb_bedrock_policy(
            self.config.kb.bedrock_policy_name,
            self.config.kb.get_embedding_model_arn(self.config.aws.region)
        )
        self.iam_mgr.attach_policy_to_role(self.config.kb.kb_role_name, bedrock_policy_arn)
        
        s3_policy_arn = self.iam_mgr.create_kb_s3_policy(
            self.config.kb.s3_policy_name,
            bucket_name
        )
        self.iam_mgr.attach_policy_to_role(self.config.kb.kb_role_name, s3_policy_arn)
        
        aoss_policy_arn = self.iam_mgr.create_kb_opensearch_policy(
            self.config.kb.aoss_policy_name,
            collection_arn
        )
        self.iam_mgr.attach_policy_to_role(self.config.kb.kb_role_name, aoss_policy_arn)
        
        # Wait for policies to propagate
        time.sleep(10)
        
        # Storage configuration
        storage_config = {
            'type': 'OPENSEARCH_SERVERLESS',
            'opensearchServerlessConfiguration': {
                'collectionArn': collection_arn,
                'vectorIndexName': self.config.kb.vector_index_name,
                'fieldMapping': {
                    'vectorField': self.config.kb.vector_field,
                    'textField': self.config.kb.text_field,
                    'metadataField': self.config.kb.metadata_field
                }
            }
        }
        
        # Create Knowledge Base
        kb_id = self.kb_mgr.create_knowledge_base(
            self.config.kb.kb_name,
            self.config.kb.kb_agent_description,
            kb_role_arn,
            storage_config,
            self.config.kb.get_embedding_model_arn(self.config.aws.region)
        )
        
        # Create data source
        data_source_config = {
            'bucketArn': f"arn:aws:s3:::{bucket_name}",
            'inclusionPrefixes': [self.config.kb.data_source_prefix]
        }
        
        ds_id = self.kb_mgr.create_data_source(
            kb_id,
            self.config.kb.data_source_name,
            'S3',
            data_source_config
        )
        
        logger.info(f"✅ Knowledge Base '{kb_id}' created with data source '{ds_id}'")
        return kb_id
    
    def setup_lambda_functions(
        self,
        lambda_role_arn: str,
        collaborator_configs: List[CollaboratorConfig]
    ) -> Dict[str, str]:
        """
        Setup Lambda functions for collaborator agents
        
        Args:
            lambda_role_arn: Lambda execution role ARN
            collaborator_configs: List of collaborator configurations
            
        Returns:
            Dictionary mapping collaborator names to Lambda ARNs
        """
        logger.info("=" * 60)
        logger.info("Setting up Lambda functions...")
        logger.info("=" * 60)
        
        lambda_arns = {}
        
        for config in collaborator_configs:
            if not config.enabled:
                logger.info(f"Skipping disabled collaborator: {config.name}")
                continue
            
            # Prepare additional files if utils code provided
            additional_files = {}
            if config.utils_code:
                additional_files['utils.py'] = config.utils_code
            
            # Create Lambda function
            lambda_arn = self.lambda_mgr.create_function(
                function_name=config.lambda_function_name,
                handler_code=config.lambda_handler_code,
                role_arn=lambda_role_arn,
                additional_files=additional_files if additional_files else None
            )
            
            # Add Bedrock invoke permission
            self.lambda_mgr.add_bedrock_invoke_permission(config.lambda_function_name)
            
            lambda_arns[config.name] = lambda_arn
            logger.info(f"✅ Lambda function created for '{config.name}'")
        
        return lambda_arns
    
    def setup_supervisor_agent(self, agent_role_arn: str) -> str:
        """
        Setup supervisor agent
        
        Args:
            agent_role_arn: Agent IAM role ARN
            
        Returns:
            Supervisor agent ID
        """
        logger.info("=" * 60)
        logger.info("Setting up supervisor agent...")
        logger.info("=" * 60)
        
        # Create supervisor agent
        supervisor_id = self.agent_mgr.create_agent(
            self.config.agent.supervisor_agent_name,
            self.config.agent.supervisor_instruction,
            self.config.agent.supervisor_description,
            agent_role_arn,
            self.config.agent.foundation_model
        )
        
        # Enable supervisor mode
        self.agent_mgr.enable_supervisor_mode(supervisor_id)
        
        logger.info(f"✅ Supervisor agent created: {supervisor_id}")
        return supervisor_id
    
    def setup_collaborator_agents(
        self,
        agent_role_arn: str,
        lambda_arns: Dict[str, str],
        collaborator_configs: List[CollaboratorConfig]
    ) -> List[Dict[str, str]]:
        """
        Setup collaborator agents
        
        Args:
            agent_role_arn: Agent IAM role ARN
            lambda_arns: Dictionary of Lambda ARNs
            collaborator_configs: List of collaborator configurations
            
        Returns:
            List of collaborator info dictionaries
        """
        logger.info("=" * 60)
        logger.info("Setting up collaborator agents...")
        logger.info("=" * 60)
        
        collaborators = []
        
        for config in collaborator_configs:
            if not config.enabled:
                continue
            
            # Create agent
            agent_id = self.agent_mgr.create_agent(
                config.name,
                config.instruction,
                config.description,
                agent_role_arn,
                self.config.agent.foundation_model
            )
            
            # Create action group
            function_schema = {'functions': config.functions}
            self.agent_mgr.create_action_group(
                agent_id,
                config.action_group_name,
                config.action_group_description,
                lambda_arns[config.name],
                function_schema
            )
            
            # Prepare agent
            self.agent_mgr.prepare_agent(agent_id)
            
            # Wait for agent to be prepared
            logger.info(f"Waiting for agent {config.name} to be fully prepared...")
            time.sleep(10)  # Give agent time to be fully prepared
            
            # Create alias
            alias_id = self.agent_mgr.create_agent_alias(
                agent_id,
                f"{config.name}-alias"
            )
            
            # Wait for alias to be ready
            logger.info(f"Waiting for alias to be ready...")
            time.sleep(5)
            
            alias_arn = self.agent_mgr.get_agent_alias_arn(agent_id, alias_id)
            
            collaborators.append({
                'agent_id': agent_id,
                'alias_id': alias_id,
                'alias_arn': alias_arn,
                'name': config.name,
                'instruction': f"{config.name} handles delegated tasks from supervisor"
            })
            
            logger.info(f"✅ Collaborator agent created: {config.name}")
        
        return collaborators
    
    def associate_collaborators_with_supervisor(
        self,
        supervisor_id: str,
        collaborators: List[Dict[str, str]]
    ):
        """
        Associate all collaborators with supervisor
        
        Args:
            supervisor_id: Supervisor agent ID
            collaborators: List of collaborator info
        """
        logger.info("=" * 60)
        logger.info("Associating collaborators with supervisor...")
        logger.info("=" * 60)
        
        # Cleanup old collaborators
        keep_names = {c['name'] for c in collaborators}
        self.agent_mgr.cleanup_old_collaborators(supervisor_id, keep_names)
        
        # Associate each collaborator
        for collab in collaborators:
            # Wait for collaborator agent to be fully PREPARED
            logger.info(f"Waiting for collaborator {collab['name']} to be PREPARED...")
            self.agent_mgr.wait_for_agent_status(collab['agent_id'], 'PREPARED', timeout=300)
            
            # Match old working code exactly - no extra parameters
            self.agent_mgr.associate_collaborator(
                supervisor_id,
                collab['alias_arn'],
                collab['name'],
                collab['instruction']
            )
            logger.info(f"✅ Associated collaborator: {collab['name']}")
        
        # Prepare supervisor
        self.agent_mgr.prepare_agent(supervisor_id)
        
        # Create supervisor alias
        supervisor_alias_id = self.agent_mgr.create_agent_alias(
            supervisor_id,
            "multi-agent-alias"
        )
        
        logger.info(f"✅ Supervisor prepared with alias: {supervisor_alias_id}")
    
    def sync_knowledge_base(self, kb_id: str, data_source_id: Optional[str] = None) -> str:
        """
        Sync Knowledge Base to ingest documents
        
        Args:
            kb_id: Knowledge Base ID
            data_source_id: Optional data source ID (will get first if not provided)
            
        Returns:
            Ingestion job ID
        """
        try:
            # Get data source ID if not provided
            if not data_source_id:
                response = self.kb_mgr.client.list_data_sources(
                    knowledgeBaseId=kb_id,
                    maxResults=1
                )
                if not response.get('dataSourceSummaries'):
                    raise ValueError(f"No data sources found for Knowledge Base {kb_id}")
                data_source_id = response['dataSourceSummaries'][0]['dataSourceId']
            
            # Ensure data_source_id is not None
            if not data_source_id:
                raise ValueError("Data source ID could not be determined")
            
            # Start ingestion job
            logger.info(f"Starting ingestion job for KB {kb_id}, data source {data_source_id}")
            job_id = self.kb_mgr.start_ingestion_job(kb_id, data_source_id)
            
            # Wait for completion
            logger.info("Waiting for ingestion to complete...")
            self.kb_mgr.wait_for_ingestion_job(kb_id, data_source_id, job_id)
            
            logger.info(f"✅ Knowledge Base sync completed: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to sync Knowledge Base: {e}")
            raise
    
    def deploy_complete_system(
        self,
        collaborator_configs: List[CollaboratorConfig],
        upload_data_to_kb: bool = False,
        data_directory: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deploy the complete multi-agent system
        
        Args:
            collaborator_configs: List of collaborator configurations
            upload_data_to_kb: Whether to upload data to Knowledge Base
            data_directory: Directory containing data to upload
            
        Returns:
            Dictionary with deployment information
        """
        logger.info("=" * 80)
        logger.info("DEPLOYING COMPLETE MULTI-AGENT ETL SYSTEM")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Step 1: Setup IAM roles
        roles = self.setup_iam_roles()
        
        # Step 2: Setup storage
        bucket_name = self.setup_storage()
        
        # Step 3: Setup OpenSearch
        collection_info = self.setup_opensearch(roles['kb_role_arn'])
        
        # Step 4: Setup Knowledge Base
        kb_id = self.setup_knowledge_base(
            roles['kb_role_arn'],
            collection_info['arn'],
            bucket_name
        )
        
        # Step 5: Setup Lambda functions
        lambda_arns = self.setup_lambda_functions(
            roles['lambda_role_arn'],
            collaborator_configs
        )
        
        # Step 6: Setup supervisor agent
        supervisor_id = self.setup_supervisor_agent(roles['agent_role_arn'])
        
        # Step 7: Setup collaborator agents
        collaborators = self.setup_collaborator_agents(
            roles['agent_role_arn'],
            lambda_arns,
            collaborator_configs
        )
        
        # Step 8: Associate Knowledge Base with supervisor
        logger.info("=" * 60)
        logger.info("Associating Knowledge Base with supervisor...")
        logger.info("=" * 60)
        self.agent_mgr.associate_knowledge_base(
            supervisor_id,
            kb_id,
            self.config.kb.kb_agent_description
        )
        logger.info(f"✅ Knowledge Base associated with supervisor")
        
        # Step 9: Associate collaborators with supervisor
        self.associate_collaborators_with_supervisor(supervisor_id, collaborators)
        
        # Step 10: Upload data to KB if requested
        if upload_data_to_kb and data_directory:
            logger.info("=" * 60)
            logger.info("Uploading data to Knowledge Base...")
            logger.info("=" * 60)
            
            count = self.storage_mgr.upload_directory(
                data_directory,
                bucket_name,
                self.config.kb.data_source_prefix
            )
            logger.info(f"✅ Uploaded {count} files to Knowledge Base")
            
            # Sync Knowledge Base
            logger.info("=" * 60)
            logger.info("Syncing Knowledge Base...")
            logger.info("=" * 60)
            self.sync_knowledge_base(kb_id)
            logger.info(f"✅ Knowledge Base synced successfully")
        
        elapsed_time = time.time() - start_time
        
        logger.info("=" * 80)
        logger.info(f"✅ DEPLOYMENT COMPLETE in {elapsed_time:.2f} seconds")
        logger.info("=" * 80)
        
        return {
            'supervisor_agent_id': supervisor_id,
            'knowledge_base_id': kb_id,
            'bucket_name': bucket_name,
            'collection_endpoint': collection_info['endpoint'],
            'collaborators': [c['name'] for c in collaborators],
            'deployment_time': elapsed_time
        }


if __name__ == "__main__":
    # Example usage
    orchestrator = MultiAgentOrchestrator()
    config.print_summary()

