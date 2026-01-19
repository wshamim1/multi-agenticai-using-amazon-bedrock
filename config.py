"""
Core Configuration Module for Smart ETL Agentic AI System
Centralizes all configuration, AWS clients, and environment setup
"""

import os
import boto3
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class AWSConfig:
    """AWS Configuration and Client Management"""
    
    # Session and region info
    session: boto3.Session = field(default_factory=boto3.Session)
    region: str = field(init=False)
    account_id: str = field(init=False)
    suffix: str = field(init=False)
    
    # AWS Clients
    iam_client: Any = field(init=False)
    s3_client: Any = field(init=False)
    lambda_client: Any = field(init=False)
    bedrock_agent_client: Any = field(init=False)
    bedrock_agent_runtime_client: Any = field(init=False)
    bedrock_runtime_client: Any = field(init=False)
    opensearch_client: Any = field(init=False)
    sts_client: Any = field(init=False)
    
    def __post_init__(self):
        """Initialize AWS clients and configuration"""
        try:
            # Get region and account info
            self.region = self.session.region_name or os.getenv('AWS_REGION', 'us-east-1')
            self.sts_client = self.session.client('sts', region_name=self.region)
            self.account_id = self.sts_client.get_caller_identity()["Account"]
            self.suffix = f"{self.region}-{self.account_id}"
            
            # Initialize all AWS clients
            self.iam_client = self.session.client('iam')
            self.s3_client = self.session.client('s3', region_name=self.region)
            self.lambda_client = self.session.client('lambda', region_name=self.region)
            self.bedrock_agent_client = self.session.client('bedrock-agent', region_name=self.region)
            self.bedrock_agent_runtime_client = self.session.client('bedrock-agent-runtime', region_name=self.region)
            self.bedrock_runtime_client = self.session.client('bedrock-runtime', region_name=self.region)
            self.opensearch_client = self.session.client('opensearchserverless', region_name=self.region)
            
            logger.info(f"AWS Configuration initialized - Region: {self.region}, Account: {self.account_id}")
            
        except ClientError as e:
            logger.error(f"Failed to initialize AWS configuration: {e}")
            raise


@dataclass
class AgentConfig:
    """Bedrock Agent Configuration"""
    
    # Base configuration
    base_name: str = "multi-agent-ai"
    foundation_model: str = "amazon.nova-pro-v1:0"  # Amazon Nova Pro 1.0
    
    # Derived names
    agent_name: str = field(init=False)
    agent_role_name: str = field(init=False)
    supervisor_agent_name: str = field(init=False)
    lambda_role_name: str = field(init=False)
    
    # Instructions and descriptions
    agent_description: str = "Multi-agent AI system for weather, stock market, and news information"
    agent_instruction: str = "You are a helpful AI assistant coordinating specialized agents for various information services"
    supervisor_instruction: str = "You are a supervisor that intelligently routes queries to specialized agents (weather, stocks, news) based on user needs"
    supervisor_description: str = "Supervisor agent coordinating weather, stock market, and news information agents"
    
    # Action group configuration
    action_group_name: str = field(init=False)
    action_group_description: str = "Action group for information retrieval operations"
    
    def __post_init__(self):
        """Initialize derived configuration values"""
        self.agent_name = f"{self.base_name}-multiagent"
        self.supervisor_agent_name = f"{self.agent_name}-supervisor"
        self.lambda_role_name = f"{self.agent_name}-lambda-role"
        self.action_group_name = f"{self.base_name}-actions"
    
    def get_agent_role_name(self, suffix: str) -> str:
        """Get agent role name with suffix"""
        return f"{self.base_name}-agent-role-{suffix}"
    
    def get_bedrock_policy_name(self, suffix: str) -> str:
        """Get Bedrock policy name with suffix"""
        return f"{self.agent_name}-bedrock-allow-{suffix}"


@dataclass
class KnowledgeBaseConfig:
    """Knowledge Base Configuration"""
    
    # Base configuration
    base_name: str = "bedrock-agent-kb"
    embedding_model: str = "amazon.titan-embed-text-v1"
    kb_model: str = "amazon.titan-text-premier-v1:0"
    
    # Derived names
    kb_name: str = field(init=False)
    collection_name: str = field(init=False)
    vector_index_name: str = field(init=False)
    data_source_name: str = field(init=False)
    
    # Index field names
    metadata_field: str = "metadata"
    text_field: str = "text"
    vector_field: str = "vector"
    
    # Data source configuration
    data_source_prefix: str = "knowledge-base/"
    
    # Agent configuration
    kb_agent_name: str = field(init=False)
    kb_agent_instruction: str = "Retrieve and summarize information from the knowledge base to answer user questions"
    kb_agent_description: str = "Knowledge base agent for document retrieval and Q&A"
    
    # IAM configuration
    kb_role_name: str = field(init=False)
    bedrock_policy_name: str = field(init=False)
    aoss_policy_name: str = field(init=False)
    s3_policy_name: str = field(init=False)
    
    def __post_init__(self):
        """Initialize derived configuration values"""
        self.kb_agent_name = f"{self.base_name}-agent"
        self.kb_role_name = f"{self.base_name}-execution-role"
    
    def initialize_with_suffix(self, suffix: str):
        """Initialize names that require AWS suffix"""
        self.kb_name = f"{self.base_name}-{suffix}"
        self.collection_name = f"{self.base_name}-collection"
        self.vector_index_name = f"{self.base_name}-index"
        self.data_source_name = f"{self.kb_name}-s3-ds"
        self.bedrock_policy_name = f"{self.base_name}-bedrock-allow-{suffix}"
        self.aoss_policy_name = f"{self.base_name}-aoss-allow-{suffix}"
        self.s3_policy_name = f"{self.base_name}-s3-allow-{suffix}"
    
    def get_embedding_model_arn(self, region: str) -> str:
        """Get embedding model ARN"""
        return f"arn:aws:bedrock:{region}::foundation-model/{self.embedding_model}"


@dataclass
class StorageConfig:
    """S3 and Storage Configuration"""
    
    base_name: str = "bedrock-agent"
    bucket_name: str = field(init=False)
    table_name: str = field(init=False)
    
    def initialize_with_suffix(self, suffix: str):
        """Initialize names that require AWS suffix"""
        self.bucket_name = f"{self.base_name}-bucket-{suffix}"
        self.table_name = f"{self.base_name}-table-{suffix}"


@dataclass
class LambdaConfig:
    """Lambda Function Configuration"""
    
    base_name: str = "bedrock-agent"
    sync_lambda_name: str = field(init=False)
    
    # Lambda runtime configuration
    runtime: str = "python3.11"
    timeout: int = 300
    memory_size: int = 512
    
    def initialize_with_suffix(self, suffix: str):
        """Initialize names that require AWS suffix"""
        self.sync_lambda_name = f"{self.base_name}-perform-sync-{suffix}"


class Config:
    """Main Configuration Class - Singleton Pattern"""
    
    _instance: Optional['Config'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize all configuration components"""
        if not hasattr(self, 'initialized'):
            # Initialize AWS configuration first
            self.aws = AWSConfig()
            
            # Initialize other configurations
            self.agent = AgentConfig()
            self.kb = KnowledgeBaseConfig()
            self.storage = StorageConfig()
            self.lambda_config = LambdaConfig()
            
            # Initialize suffix-dependent names
            self.kb.initialize_with_suffix(self.aws.suffix)
            self.storage.initialize_with_suffix(self.aws.suffix)
            self.lambda_config.initialize_with_suffix(self.aws.suffix)
            
            self.initialized = True
            logger.info("Configuration initialized successfully")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            "region": self.aws.region,
            "account_id": self.aws.account_id,
            "agent_name": self.agent.agent_name,
            "supervisor_name": self.agent.supervisor_agent_name,
            "kb_name": self.kb.kb_name,
            "bucket_name": self.storage.bucket_name,
            "collection_name": self.kb.collection_name
        }
    
    def print_summary(self):
        """Print configuration summary"""
        summary = self.get_summary()
        logger.info("=" * 60)
        logger.info("Configuration Summary")
        logger.info("=" * 60)
        for key, value in summary.items():
            logger.info(f"{key:20s}: {value}")
        logger.info("=" * 60)


# Global configuration instance
config = Config()


if __name__ == "__main__":
    # Test configuration
    config.print_summary()

# Made with Bob
