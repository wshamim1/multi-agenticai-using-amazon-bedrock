"""
Cleanup Script
Deletes all AWS resources created by the multi-agent system
"""

import logging
import time
from typing import List, Set
from botocore.exceptions import ClientError

from config import config
from core.iam_manager import IAMManager
from core.storage_manager import StorageManager
from core.lambda_manager import LambdaManager
from core.opensearch_manager import OpenSearchManager
from core.knowledge_base_manager import KnowledgeBaseManager
from core.agent_manager import AgentManager

logger = logging.getLogger(__name__)


class ResourceCleanup:
    """Handles cleanup of all AWS resources"""
    
    def __init__(self):
        """Initialize cleanup with all managers"""
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
    
    def cleanup_agents(self):
        """Delete all Bedrock agents"""
        logger.info("=" * 60)
        logger.info("Cleaning up Bedrock Agents...")
        logger.info("=" * 60)
        
        try:
            # Get all agents
            response = self.agent_mgr.client.list_agents(maxResults=100)
            agents = response.get('agentSummaries', [])
            
            for agent in agents:
                agent_name = agent['agentName']
                agent_id = agent['agentId']
                
                # Check if it's one of our agents
                if agent_name.startswith(self.config.agent.base_name):
                    logger.info(f"Deleting agent: {agent_name} ({agent_id})")
                    self.agent_mgr.delete_agent(agent_id)
                    time.sleep(2)
            
            logger.info("✅ Agents cleanup completed")
            
        except Exception as e:
            logger.error(f"Error cleaning up agents: {e}")
    
    def cleanup_knowledge_bases(self):
        """Delete all Knowledge Bases"""
        logger.info("=" * 60)
        logger.info("Cleaning up Knowledge Bases...")
        logger.info("=" * 60)
        
        try:
            # Get all knowledge bases
            kbs = self.kb_mgr.list_knowledge_bases()
            
            for kb in kbs:
                kb_name = kb['name']
                kb_id = kb['knowledgeBaseId']
                
                # Check if it's one of our KBs
                if kb_name.startswith(self.config.kb.base_name):
                    logger.info(f"Deleting Knowledge Base: {kb_name} ({kb_id})")
                    self.kb_mgr.delete_knowledge_base(kb_id)
                    time.sleep(2)
            
            logger.info("✅ Knowledge Bases cleanup completed")
            
        except Exception as e:
            logger.error(f"Error cleaning up Knowledge Bases: {e}")
    
    def cleanup_opensearch(self):
        """Delete OpenSearch collections and policies"""
        logger.info("=" * 60)
        logger.info("Cleaning up OpenSearch...")
        logger.info("=" * 60)
        
        try:
            collection_name = self.config.kb.collection_name
            
            # Delete collection first
            logger.info(f"Deleting OpenSearch collection: {collection_name}")
            self.opensearch_mgr.delete_collection(collection_name)
            time.sleep(5)
            
            # Delete all policies associated with the collection
            # List and delete by pattern matching instead of hardcoded names
            logger.info("Deleting OpenSearch policies...")
            self._delete_opensearch_policies(collection_name)
            
            logger.info("✅ OpenSearch cleanup completed")
            
        except Exception as e:
            logger.error(f"Error cleaning up OpenSearch: {e}")
    
    def _delete_opensearch_policies(self, collection_name: str):
        """
        Delete all OpenSearch policies associated with a collection
        
        Args:
            collection_name: Name of the collection
        """
        try:
            # Delete encryption policies
            logger.info("Listing and deleting encryption policies...")
            try:
                response = self.config.aws.opensearch_client.list_security_policies(
                    type='encryption',
                    resource=[collection_name]
                )
                for policy in response.get('securityPolicySummaries', []):
                    policy_name = policy['name']
                    try:
                        self.opensearch_mgr.delete_security_policy(policy_name, 'encryption')
                    except Exception as e:
                        logger.warning(f"Could not delete encryption policy '{policy_name}': {e}")
            except Exception as e:
                logger.warning(f"Error listing encryption policies: {e}")
            
            # Delete network policies
            logger.info("Listing and deleting network policies...")
            try:
                response = self.config.aws.opensearch_client.list_security_policies(
                    type='network',
                    resource=[collection_name]
                )
                for policy in response.get('securityPolicySummaries', []):
                    policy_name = policy['name']
                    try:
                        self.opensearch_mgr.delete_security_policy(policy_name, 'network')
                    except Exception as e:
                        logger.warning(f"Could not delete network policy '{policy_name}': {e}")
            except Exception as e:
                logger.warning(f"Error listing network policies: {e}")
            
            # Delete data access policies
            logger.info("Listing and deleting data access policies...")
            try:
                response = self.config.aws.opensearch_client.list_access_policies(
                    type='data',
                    resource=[collection_name]
                )
                for policy in response.get('accessPolicySummaries', []):
                    policy_name = policy['name']
                    try:
                        self.opensearch_mgr.delete_access_policy(policy_name)
                    except Exception as e:
                        logger.warning(f"Could not delete access policy '{policy_name}': {e}")
            except Exception as e:
                logger.warning(f"Error listing access policies: {e}")
                
        except Exception as e:
            logger.error(f"Error deleting OpenSearch policies: {e}")
    
    def cleanup_lambda_functions(self):
        """Delete all Lambda functions"""
        logger.info("=" * 60)
        logger.info("Cleaning up Lambda Functions...")
        logger.info("=" * 60)
        
        try:
            # List all Lambda functions with our prefix
            functions = self.lambda_mgr.list_functions(
                prefix=self.config.agent.base_name
            )
            
            for func in functions:
                func_name = func['name']
                logger.info(f"Deleting Lambda function: {func_name}")
                self.lambda_mgr.delete_function(func_name)
                time.sleep(1)
            
            logger.info("✅ Lambda Functions cleanup completed")
            
        except Exception as e:
            logger.error(f"Error cleaning up Lambda functions: {e}")
    
    def cleanup_s3_buckets(self):
        """Delete S3 buckets"""
        logger.info("=" * 60)
        logger.info("Cleaning up S3 Buckets...")
        logger.info("=" * 60)
        
        try:
            bucket_name = self.config.storage.bucket_name
            
            logger.info(f"Deleting S3 bucket: {bucket_name}")
            self.storage_mgr.delete_bucket(bucket_name, force=True)
            
            logger.info("✅ S3 Buckets cleanup completed")
            
        except Exception as e:
            logger.error(f"Error cleaning up S3 buckets: {e}")
    
    def cleanup_iam_roles_and_policies(self):
        """Delete IAM roles and policies"""
        logger.info("=" * 60)
        logger.info("Cleaning up IAM Roles and Policies...")
        logger.info("=" * 60)
        
        try:
            # Agent role
            agent_role_name = self.config.agent.get_agent_role_name(self.config.aws.suffix)
            logger.info(f"Deleting IAM role: {agent_role_name}")
            self.iam_mgr.delete_role(agent_role_name)
            
            # Lambda role
            lambda_role_name = self.config.agent.lambda_role_name
            logger.info(f"Deleting IAM role: {lambda_role_name}")
            self.iam_mgr.delete_role(lambda_role_name)
            
            # KB role
            kb_role_name = self.config.kb.kb_role_name
            logger.info(f"Deleting IAM role: {kb_role_name}")
            self.iam_mgr.delete_role(kb_role_name)
            
            # Delete policies
            logger.info("Deleting IAM policies...")
            
            # Agent policy
            agent_policy_name = self.config.agent.get_bedrock_policy_name(self.config.aws.suffix)
            self.iam_mgr.delete_policy(agent_policy_name)
            
            # KB policies
            self.iam_mgr.delete_policy(self.config.kb.bedrock_policy_name)
            self.iam_mgr.delete_policy(self.config.kb.aoss_policy_name)
            self.iam_mgr.delete_policy(self.config.kb.s3_policy_name)
            
            logger.info("✅ IAM cleanup completed")
            
        except Exception as e:
            logger.error(f"Error cleaning up IAM: {e}")
    
    def cleanup_all(self):
        """
        Clean up all resources in the correct order
        """
        logger.info("\n" + "=" * 80)
        logger.info("STARTING COMPLETE RESOURCE CLEANUP")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Order matters - delete in reverse order of creation
        try:
            # 1. Delete agents first (they depend on other resources)
            self.cleanup_agents()
            time.sleep(5)
            
            # 2. Delete Knowledge Bases
            self.cleanup_knowledge_bases()
            time.sleep(5)
            
            # 3. Delete OpenSearch
            self.cleanup_opensearch()
            time.sleep(5)
            
            # 4. Delete Lambda functions
            self.cleanup_lambda_functions()
            time.sleep(5)
            
            # 5. Delete S3 buckets
            self.cleanup_s3_buckets()
            time.sleep(5)
            
            # 6. Delete IAM roles and policies (last, as they're used by everything)
            self.cleanup_iam_roles_and_policies()
            
            elapsed_time = time.time() - start_time
            
            logger.info("\n" + "=" * 80)
            logger.info(f"✅ CLEANUP COMPLETED in {elapsed_time:.2f} seconds")
            logger.info("=" * 80)
            logger.info("\nAll resources have been deleted successfully!")
            logger.info("You can now safely delete the TO_BE_DELETED folders.")
            
        except Exception as e:
            logger.error(f"\n❌ Cleanup failed: {e}")
            logger.error("Some resources may not have been deleted.")
            logger.error("Please check AWS Console and delete manually if needed.")
            raise


def cleanup_all_resources():
    """
    Main cleanup function
    """
    cleanup = ResourceCleanup()
    cleanup.cleanup_all()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Confirm before cleanup
    print("\n" + "=" * 80)
    print("⚠️  WARNING: This will delete ALL resources created by the system!")
    print("=" * 80)
    print("\nThis includes:")
    print("  - Bedrock Agents (supervisor and collaborators)")
    print("  - Knowledge Bases and data sources")
    print("  - OpenSearch Serverless collections")
    print("  - Lambda functions")
    print("  - S3 buckets (and all contents)")
    print("  - IAM roles and policies")
    print("\n" + "=" * 80)
    
    response = input("\nAre you sure you want to proceed? (yes/no): ")
    
    if response.lower() == 'yes':
        cleanup_all_resources()
    else:
        print("\nCleanup cancelled.")

