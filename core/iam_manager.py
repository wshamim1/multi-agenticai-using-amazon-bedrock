"""
IAM Role and Policy Management Module
Handles creation and management of IAM roles and policies for Bedrock agents, Lambda functions, and Knowledge Bases
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class IAMManager:
    """Manages IAM roles and policies for the ETL system"""
    
    def __init__(self, iam_client, account_id: str, region: str):
        """
        Initialize IAM Manager
        
        Args:
            iam_client: Boto3 IAM client
            account_id: AWS account ID
            region: AWS region
        """
        self.iam_client = iam_client
        self.account_id = account_id
        self.region = region
    
    def create_role(
        self,
        role_name: str,
        assume_role_policy: Dict[str, Any],
        description: str = ""
    ) -> str:
        """
        Create IAM role or return existing role ARN
        
        Args:
            role_name: Name of the IAM role
            assume_role_policy: Trust policy document
            description: Role description
            
        Returns:
            Role ARN
        """
        try:
            # Check if role exists
            response = self.iam_client.get_role(RoleName=role_name)
            role_arn = response['Role']['Arn']
            logger.info(f"IAM role '{role_name}' already exists: {role_arn}")
            return role_arn
            
        except self.iam_client.exceptions.NoSuchEntityException:
            # Create new role
            try:
                response = self.iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(assume_role_policy),
                    Description=description,
                    MaxSessionDuration=3600
                )
                role_arn = response['Role']['Arn']
                logger.info(f"Created IAM role '{role_name}': {role_arn}")
                
                # Wait for role to be available
                time.sleep(10)
                return role_arn
                
            except ClientError as e:
                logger.error(f"Failed to create IAM role '{role_name}': {e}")
                raise
    
    def create_policy(
        self,
        policy_name: str,
        policy_document: Dict[str, Any],
        description: str = ""
    ) -> str:
        """
        Create IAM policy or return existing policy ARN
        
        Args:
            policy_name: Name of the IAM policy
            policy_document: Policy document
            description: Policy description
            
        Returns:
            Policy ARN
        """
        policy_arn = f"arn:aws:iam::{self.account_id}:policy/{policy_name}"
        
        try:
            # Check if policy exists
            self.iam_client.get_policy(PolicyArn=policy_arn)
            logger.info(f"IAM policy '{policy_name}' already exists: {policy_arn}")
            return policy_arn
            
        except self.iam_client.exceptions.NoSuchEntityException:
            # Create new policy
            try:
                response = self.iam_client.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_document),
                    Description=description
                )
                policy_arn = response['Policy']['Arn']
                logger.info(f"Created IAM policy '{policy_name}': {policy_arn}")
                return policy_arn
                
            except ClientError as e:
                logger.error(f"Failed to create IAM policy '{policy_name}': {e}")
                raise
    
    def attach_policy_to_role(self, role_name: str, policy_arn: str):
        """
        Attach policy to role
        
        Args:
            role_name: Name of the IAM role
            policy_arn: ARN of the policy to attach
        """
        try:
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            logger.info(f"Attached policy '{policy_arn}' to role '{role_name}'")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                logger.info(f"Policy '{policy_arn}' already attached to role '{role_name}'")
            else:
                logger.error(f"Failed to attach policy to role: {e}")
                raise
    
    def create_bedrock_agent_role(self, role_name: str, agent_name: str) -> str:
        """
        Create IAM role for Bedrock agent
        
        Args:
            role_name: Name of the IAM role
            agent_name: Name of the agent
            
        Returns:
            Role ARN
        """
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "StringEquals": {
                            "aws:SourceAccount": self.account_id
                        },
                        "ArnLike": {
                            "aws:SourceArn": f"arn:aws:bedrock:{self.region}:{self.account_id}:agent/*"
                        }
                    }
                }
            ]
        }
        
        return self.create_role(
            role_name=role_name,
            assume_role_policy=assume_role_policy,
            description=f"IAM role for Bedrock agent: {agent_name}"
        )
    
    def create_bedrock_agent_policy(
        self,
        policy_name: str,
        foundation_model: str
    ) -> str:
        """
        Create policy for Bedrock agent to invoke foundation models and collaborate with other agents
        
        Args:
            policy_name: Name of the policy
            foundation_model: Foundation model ID
            
        Returns:
            Policy ARN
        """
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "BedrockMultiAgentCollaboration",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:AssociateAgentCollaborator",
                        "bedrock:InvokeAgent",
                        "bedrock:GetAgent",
                        "bedrock:GetAgentAlias",
                        "bedrock:ListAgentAliases"
                    ],
                    "Resource": "*"
                },
                {
                    "Sid": "BedrockKnowledgeBaseAccess",
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:Retrieve",
                        "bedrock:RetrieveAndGenerate"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        return self.create_policy(
            policy_name=policy_name,
            policy_document=policy_document,
            description="Allow Bedrock agent to invoke foundation models and collaborate with other agents"
        )
    
    def create_lambda_execution_role(self, role_name: str) -> str:
        """
        Create IAM role for Lambda function execution
        
        Args:
            role_name: Name of the IAM role
            
        Returns:
            Role ARN
        """
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        role_arn = self.create_role(
            role_name=role_name,
            assume_role_policy=assume_role_policy,
            description="IAM role for Lambda function execution"
        )
        
        # Attach basic Lambda execution policy
        self.attach_policy_to_role(
            role_name=role_name,
            policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        
        return role_arn
    
    def create_kb_execution_role(self, role_name: str) -> str:
        """
        Create IAM role for Knowledge Base execution
        
        Args:
            role_name: Name of the IAM role
            
        Returns:
            Role ARN
        """
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "bedrock.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "StringEquals": {
                            "aws:SourceAccount": self.account_id
                        },
                        "ArnLike": {
                            "aws:SourceArn": f"arn:aws:bedrock:{self.region}:{self.account_id}:knowledge-base/*"
                        }
                    }
                }
            ]
        }
        
        return self.create_role(
            role_name=role_name,
            assume_role_policy=assume_role_policy,
            description="IAM role for Knowledge Base execution"
        )
    
    def create_kb_bedrock_policy(
        self,
        policy_name: str,
        embedding_model_arn: str
    ) -> str:
        """
        Create policy for Knowledge Base to access Bedrock
        
        Args:
            policy_name: Name of the policy
            embedding_model_arn: ARN of the embedding model
            
        Returns:
            Policy ARN
        """
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "bedrock:InvokeModel",
                    "Resource": embedding_model_arn
                }
            ]
        }
        
        return self.create_policy(
            policy_name=policy_name,
            policy_document=policy_document,
            description="Allow Knowledge Base to invoke embedding model"
        )
    
    def create_kb_s3_policy(
        self,
        policy_name: str,
        bucket_name: str
    ) -> str:
        """
        Create policy for Knowledge Base to access S3
        
        Args:
            policy_name: Name of the policy
            bucket_name: S3 bucket name
            
        Returns:
            Policy ARN
        """
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{bucket_name}",
                        f"arn:aws:s3:::{bucket_name}/*"
                    ]
                }
            ]
        }
        
        return self.create_policy(
            policy_name=policy_name,
            policy_document=policy_document,
            description="Allow Knowledge Base to access S3 bucket"
        )
    
    def create_kb_opensearch_policy(
        self,
        policy_name: str,
        collection_arn: str
    ) -> str:
        """
        Create policy for Knowledge Base to access OpenSearch
        
        Args:
            policy_name: Name of the policy
            collection_arn: OpenSearch collection ARN
            
        Returns:
            Policy ARN
        """
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "aoss:APIAccessAll",
                    "Resource": collection_arn
                }
            ]
        }
        
        return self.create_policy(
            policy_name=policy_name,
            policy_document=policy_document,
            description="Allow Knowledge Base to access OpenSearch collection"
        )
    
    def update_agent_policy_with_collaborators(
        self,
        policy_name: str,
        agent_alias_arns: List[str]
    ):
        """
        Update agent policy to allow invoking collaborator agents
        
        Args:
            policy_name: Name of the policy to update
            agent_alias_arns: List of agent alias ARNs
        """
        policy_arn = f"arn:aws:iam::{self.account_id}:policy/{policy_name}"
        
        try:
            # Get current policy version
            response = self.iam_client.get_policy(PolicyArn=policy_arn)
            current_version = response['Policy']['DefaultVersionId']
            
            # Get policy document
            policy_response = self.iam_client.get_policy_version(
                PolicyArn=policy_arn,
                VersionId=current_version
            )
            policy_doc = json.loads(policy_response['PolicyVersion']['Document'])
            
            # Add statement for agent invocation
            invoke_statement = {
                "Effect": "Allow",
                "Action": "bedrock:InvokeAgent",
                "Resource": agent_alias_arns
            }
            
            # Check if statement already exists
            statements = policy_doc.get('Statement', [])
            if not any(s.get('Action') == 'bedrock:InvokeAgent' for s in statements):
                statements.append(invoke_statement)
                policy_doc['Statement'] = statements
                
                # Create new policy version
                self.iam_client.create_policy_version(
                    PolicyArn=policy_arn,
                    PolicyDocument=json.dumps(policy_doc),
                    SetAsDefault=True
                )
                logger.info(f"Updated policy '{policy_name}' with agent invocation permissions")
            else:
                logger.info(f"Policy '{policy_name}' already has agent invocation permissions")
                
        except ClientError as e:
            logger.error(f"Failed to update policy '{policy_name}': {e}")
            raise
    
    def delete_role(self, role_name: str):
        """
        Delete IAM role and detach all policies
        
        Args:
            role_name: Name of the IAM role
        """
        try:
            # Detach all managed policies
            response = self.iam_client.list_attached_role_policies(RoleName=role_name)
            for policy in response['AttachedPolicies']:
                self.iam_client.detach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy['PolicyArn']
                )
                logger.info(f"Detached policy '{policy['PolicyArn']}' from role '{role_name}'")
            
            # Delete inline policies
            response = self.iam_client.list_role_policies(RoleName=role_name)
            for policy_name in response['PolicyNames']:
                self.iam_client.delete_role_policy(
                    RoleName=role_name,
                    PolicyName=policy_name
                )
                logger.info(f"Deleted inline policy '{policy_name}' from role '{role_name}'")
            
            # Delete role
            self.iam_client.delete_role(RoleName=role_name)
            logger.info(f"Deleted IAM role '{role_name}'")
            
        except self.iam_client.exceptions.NoSuchEntityException:
            logger.info(f"IAM role '{role_name}' does not exist")
        except ClientError as e:
            logger.error(f"Failed to delete IAM role '{role_name}': {e}")
            raise
    
    def delete_policy(self, policy_name: str):
        """
        Delete IAM policy
        
        Args:
            policy_name: Name of the IAM policy
        """
        policy_arn = f"arn:aws:iam::{self.account_id}:policy/{policy_name}"
        
        try:
            # Delete all non-default versions first
            response = self.iam_client.list_policy_versions(PolicyArn=policy_arn)
            for version in response['Versions']:
                if not version['IsDefaultVersion']:
                    self.iam_client.delete_policy_version(
                        PolicyArn=policy_arn,
                        VersionId=version['VersionId']
                    )
            
            # Delete policy
            self.iam_client.delete_policy(PolicyArn=policy_arn)
            logger.info(f"Deleted IAM policy '{policy_name}'")
            
        except self.iam_client.exceptions.NoSuchEntityException:
            logger.info(f"IAM policy '{policy_name}' does not exist")
        except ClientError as e:
            logger.error(f"Failed to delete IAM policy '{policy_name}': {e}")
            raise

