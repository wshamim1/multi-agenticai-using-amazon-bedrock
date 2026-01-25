"""
Bedrock Agent Management Module
Handles creation and management of Bedrock agents, action groups, and collaborators
"""

import time
import json
import logging
from typing import Dict, Any, Optional, List, Set
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class AgentManager:
    """Manages Bedrock Agent operations"""
    
    def __init__(
        self,
        bedrock_agent_client,
        bedrock_agent_runtime_client,
        account_id: str,
        region: str
    ):
        """
        Initialize Agent Manager
        
        Args:
            bedrock_agent_client: Boto3 Bedrock Agent client
            bedrock_agent_runtime_client: Boto3 Bedrock Agent Runtime client
            account_id: AWS account ID
            region: AWS region
        """
        self.client = bedrock_agent_client
        self.runtime_client = bedrock_agent_runtime_client
        self.account_id = account_id
        self.region = region
    
    def create_agent(
        self,
        agent_name: str,
        agent_instruction: str,
        agent_description: str,
        role_arn: str,
        foundation_model: str,
        idle_session_ttl: int = 1800
    ) -> str:
        """
        Create Bedrock agent
        
        Args:
            agent_name: Name of the agent
            agent_instruction: Agent instructions
            agent_description: Agent description
            role_arn: IAM role ARN
            foundation_model: Foundation model ID
            idle_session_ttl: Idle session TTL in seconds
            
        Returns:
            Agent ID
        """
        try:
            # Check if agent exists
            existing_agent = self.get_agent_by_name(agent_name)
            if existing_agent:
                agent_id = existing_agent['agentId']
                logger.info(f"Agent '{agent_name}' already exists: {agent_id}")
                return agent_id
            
            # Create agent
            response = self.client.create_agent(
                agentName=agent_name,
                agentResourceRoleArn=role_arn,
                description=agent_description,
                instruction=agent_instruction,
                foundationModel=foundation_model,
                idleSessionTTLInSeconds=idle_session_ttl
            )
            
            agent_id = response['agent']['agentId']
            logger.info(f"Created agent '{agent_name}': {agent_id}")
            
            # Wait for agent to be ready
            time.sleep(5)
            
            return agent_id
            
        except ClientError as e:
            logger.error(f"Failed to create agent: {e}")
            raise
    
    def update_agent(
        self,
        agent_id: str,
        agent_name: str,
        agent_instruction: str,
        agent_description: str,
        role_arn: str,
        foundation_model: str,
        memory_configuration: Optional[Dict[str, Any]] = None,
        agent_collaboration: Optional[str] = None
    ) -> bool:
        """
        Update agent configuration
        
        Args:
            agent_id: Agent ID
            agent_name: Agent name
            agent_instruction: Agent instructions
            agent_description: Agent description
            role_arn: IAM role ARN
            foundation_model: Foundation model ID
            memory_configuration: Memory configuration
            agent_collaboration: Collaboration mode (e.g., 'SUPERVISOR_ROUTER')
            
        Returns:
            True if update successful
        """
        try:
            update_params = {
                'agentId': agent_id,
                'agentName': agent_name,
                'agentResourceRoleArn': role_arn,
                'description': agent_description,
                'instruction': agent_instruction,
                'foundationModel': foundation_model
            }
            
            if memory_configuration:
                update_params['memoryConfiguration'] = memory_configuration
            
            if agent_collaboration:
                update_params['agentCollaboration'] = agent_collaboration
            
            self.client.update_agent(**update_params)
            logger.info(f"Updated agent: {agent_id}")
            
            return True
            
        except ClientError as e:
            logger.error(f"Failed to update agent: {e}")
            raise
    
    def enable_supervisor_mode(
        self,
        agent_id: str,
        enable_session_summary: bool = True
    ) -> bool:
        """
        Enable supervisor mode for an agent
        
        Args:
            agent_id: Agent ID
            enable_session_summary: Enable session summary memory
            
        Returns:
            True if successful
        """
        try:
            # Get current agent configuration
            response = self.client.get_agent(agentId=agent_id)
            agent = response['agent']
            
            # Configure memory
            memory_config = agent.get('memoryConfiguration', {})
            enabled_memory_types = memory_config.get('enabledMemoryTypes', [])
            
            if enable_session_summary and 'SESSION_SUMMARY' not in enabled_memory_types:
                enabled_memory_types.append('SESSION_SUMMARY')
                memory_config['enabledMemoryTypes'] = enabled_memory_types
            
            # Update agent with supervisor mode
            self.update_agent(
                agent_id=agent_id,
                agent_name=agent['agentName'],
                agent_instruction=agent.get('instruction', ''),
                agent_description=agent.get('description', ''),
                role_arn=agent['agentResourceRoleArn'],
                foundation_model=agent['foundationModel'],
                memory_configuration=memory_config,
                agent_collaboration='SUPERVISOR_ROUTER'
            )
            
            logger.info(f"Enabled supervisor mode for agent: {agent_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to enable supervisor mode: {e}")
            raise
    
    def create_action_group(
        self,
        agent_id: str,
        action_group_name: str,
        action_group_description: str,
        lambda_function_arn: str,
        function_schema: Dict[str, Any],
        action_group_state: str = "ENABLED"
    ) -> str:
        """
        Create action group for agent
        
        Args:
            agent_id: Agent ID
            action_group_name: Name of the action group
            action_group_description: Description
            lambda_function_arn: Lambda function ARN
            function_schema: Function schema definition
            action_group_state: State (ENABLED/DISABLED)
            
        Returns:
            Action group ID
        """
        try:
            # Check if action group exists
            existing_ag = self.get_action_group_by_name(agent_id, action_group_name)
            if existing_ag:
                ag_id = existing_ag['actionGroupId']
                logger.info(f"Action group '{action_group_name}' already exists: {ag_id}")
                
                # Update existing action group
                self.client.update_agent_action_group(
                    agentId=agent_id,
                    agentVersion='DRAFT',
                    actionGroupId=ag_id,
                    actionGroupName=action_group_name,
                    description=action_group_description,
                    actionGroupExecutor={'lambda': lambda_function_arn},
                    functionSchema=function_schema,
                    actionGroupState=action_group_state
                )
                logger.info(f"Updated action group: {ag_id}")
                return ag_id
            
            # Create new action group
            response = self.client.create_agent_action_group(
                agentId=agent_id,
                agentVersion='DRAFT',
                actionGroupName=action_group_name,
                description=action_group_description,
                actionGroupExecutor={'lambda': lambda_function_arn},
                functionSchema=function_schema,
                actionGroupState=action_group_state
            )
            
            # Response key is 'agentActionGroup' not 'actionGroup'
            ag_id = response['agentActionGroup']['actionGroupId']
            logger.info(f"Created action group '{action_group_name}': {ag_id}")
            
            return ag_id
            
        except ClientError as e:
            logger.error(f"Failed to create action group: {e}")
            raise
    
    def associate_knowledge_base(
        self,
        agent_id: str,
        kb_id: str,
        kb_description: str,
        kb_state: str = "ENABLED"
    ) -> str:
        """
        Associate Knowledge Base with agent
        
        Args:
            agent_id: Agent ID
            kb_id: Knowledge Base ID
            kb_description: Description
            kb_state: State (ENABLED/DISABLED)
            
        Returns:
            Association ID
        """
        try:
            # Check if already associated
            response = self.client.list_agent_knowledge_bases(
                agentId=agent_id,
                agentVersion='DRAFT',
                maxResults=10
            )
            
            for kb in response.get('agentKnowledgeBaseSummaries', []):
                if kb['knowledgeBaseId'] == kb_id:
                    logger.info(f"Knowledge Base {kb_id} already associated with agent {agent_id}")
                    return kb['knowledgeBaseId']
            
            # Associate KB
            response = self.client.associate_agent_knowledge_base(
                agentId=agent_id,
                agentVersion='DRAFT',
                knowledgeBaseId=kb_id,
                description=kb_description,
                knowledgeBaseState=kb_state
            )
            
            logger.info(f"Associated Knowledge Base {kb_id} with agent {agent_id}")
            return response['agentKnowledgeBase']['knowledgeBaseId']
            
        except ClientError as e:
            logger.error(f"Failed to associate Knowledge Base: {e}")
            raise
    
    def prepare_agent(self, agent_id: str) -> bool:
        """
        Prepare agent for use
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if preparation successful
        """
        try:
            self.client.prepare_agent(agentId=agent_id)
            logger.info(f"Preparing agent: {agent_id}")
            
            # Wait for agent to be prepared
            self._wait_for_agent_status(agent_id, 'PREPARED')
            
            return True
            
        except ClientError as e:
            logger.error(f"Failed to prepare agent: {e}")
            raise
    
    def create_agent_alias(
        self,
        agent_id: str,
        alias_name: str,
        description: str = ""
    ) -> str:
        """
        Create agent alias
        
        Args:
            agent_id: Agent ID
            alias_name: Alias name
            description: Alias description
            
        Returns:
            Alias ID
        """
        try:
            # Check if alias exists
            response = self.client.list_agent_aliases(
                agentId=agent_id,
                maxResults=10
            )
            
            for alias in response.get('agentAliasSummaries', []):
                if alias['agentAliasName'] == alias_name:
                    alias_id = alias['agentAliasId']
                    logger.info(f"Alias '{alias_name}' already exists: {alias_id}")
                    return alias_id
            
            # Create alias
            response = self.client.create_agent_alias(
                agentId=agent_id,
                agentAliasName=alias_name,
                description=description or f"Alias for {alias_name}"
            )
            
            alias_id = response['agentAlias']['agentAliasId']
            logger.info(f"Created alias '{alias_name}': {alias_id}")
            
            # Wait for alias to be prepared
            self._wait_for_alias_status(agent_id, alias_id, 'PREPARED')
            
            return alias_id
            
        except ClientError as e:
            logger.error(f"Failed to create agent alias: {e}")
            raise
    
    def get_agent_alias_arn(self, agent_id: str, alias_id: str) -> str:
        """
        Get agent alias ARN from AWS (not constructed manually)
        
        Args:
            agent_id: Agent ID
            alias_id: Alias ID
            
        Returns:
            Alias ARN from AWS API
        """
        try:
            response = self.client.get_agent_alias(
                agentId=agent_id,
                agentAliasId=alias_id
            )
            arn = response['agentAlias']['agentAliasArn']
            logger.info(f"Retrieved alias ARN from AWS: {arn}")
            return arn
        except ClientError as e:
            logger.error(f"Failed to get agent alias ARN: {e}")
            raise
    
    def wait_for_agent_status(
        self,
        agent_id: str,
        desired_status: str = 'PREPARED',
        timeout: int = 300,
        interval: int = 10
    ):
        """
        Wait for agent to reach desired status
        
        Args:
            agent_id: Agent ID
            desired_status: Desired status (e.g., 'PREPARED')
            timeout: Maximum wait time in seconds
            interval: Check interval in seconds
        """
        import time
        
        logger.info(f"Waiting for agent '{agent_id}' to reach status '{desired_status}'...")
        elapsed = 0
        
        while elapsed < timeout:
            try:
                response = self.client.get_agent(agentId=agent_id)
                current_status = response.get('agent', {}).get('agentStatus', '')
                
                logger.debug(f"Current status: {current_status}")
                
                if current_status == desired_status:
                    logger.info(f"Agent '{agent_id}' reached status '{desired_status}'")
                    return
                elif current_status == 'FAILED':
                    raise RuntimeError(f"Agent '{agent_id}' preparation failed.")
                    
            except ClientError as e:
                logger.warning(f"Error checking agent status: {e}")
            
            time.sleep(interval)
            elapsed += interval
        
        raise TimeoutError(f"Timeout: Agent '{agent_id}' did not reach status '{desired_status}' within {timeout} seconds.")
    
    def allow_agent_collaboration(
        self,
        collaborator_agent_id: str,
        collaborator_alias_id: str,
        supervisor_agent_id: str
    ):
        """
        Add resource policy to allow supervisor to invoke collaborator
        
        Args:
            collaborator_agent_id: Collaborator agent ID
            collaborator_alias_id: Collaborator alias ID
            supervisor_agent_id: Supervisor agent ID
        """
        try:
            # Create resource policy to allow supervisor to invoke this collaborator
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowSupervisorInvoke",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "bedrock.amazonaws.com"
                        },
                        "Action": "bedrock:InvokeAgent",
                        "Resource": f"arn:aws:bedrock:{self.region}:{self.account_id}:agent-alias/{collaborator_agent_id}/{collaborator_alias_id}",
                        "Condition": {
                            "StringEquals": {
                                "aws:SourceAccount": self.account_id
                            },
                            "ArnEquals": {
                                "aws:SourceArn": f"arn:aws:bedrock:{self.region}:{self.account_id}:agent/{supervisor_agent_id}"
                            }
                        }
                    }
                ]
            }
            
            import json
            self.client.put_agent_alias_resource_policy(
                agentId=collaborator_agent_id,
                agentAliasId=collaborator_alias_id,
                resourcePolicy=json.dumps(policy)
            )
            logger.info(f"Added resource policy to allow supervisor {supervisor_agent_id} to invoke collaborator {collaborator_agent_id}")
            
        except Exception as e:
            logger.warning(f"Could not add resource policy: {e}")
    
    def associate_collaborator(
        self,
        supervisor_agent_id: str,
        collaborator_alias_arn: str,
        collaborator_name: str,
        collaborator_instruction: str
    ) -> str:
        """
        Associate collaborator agent with supervisor
        
        Args:
            supervisor_agent_id: Supervisor agent ID
            collaborator_alias_arn: Collaborator agent alias ARN
            collaborator_name: Collaborator name
            collaborator_instruction: Instructions for collaboration
            
        Returns:
            Association ID
        """
        try:
            # Check if already associated
            existing = self.get_collaborator_by_name(supervisor_agent_id, collaborator_name)
            if existing:
                logger.info(f"Collaborator '{collaborator_name}' already associated")
                return existing['agentId']
            
            # Associate collaborator (matching old working code exactly)
            logger.info(f"Associating collaborator: {collaborator_name}")
            logger.info(f"  Supervisor Agent ID: {supervisor_agent_id}")
            logger.info(f"  Collaborator Alias ARN: {collaborator_alias_arn}")
            logger.info(f"  Collaborator Name: {collaborator_name}")
            logger.info(f"  Instruction: {collaborator_instruction}")
            
            response = self.client.associate_agent_collaborator(
                agentId=supervisor_agent_id,
                agentVersion='DRAFT',
                agentDescriptor={
                    'aliasArn': collaborator_alias_arn
                },
                collaboratorName=collaborator_name,
                collaborationInstruction=collaborator_instruction
            )
            
            collab_id = response['agentCollaborator']['agentId']
            logger.info(f"✅ Associated collaborator '{collaborator_name}' to supervisor agent '{supervisor_agent_id}'")
            
            return collab_id
            
        except self.client.exceptions.ConflictException:
            logger.warning(f"ConflictException: Collaborator '{collaborator_name}' already associated. Skipping.")
            return None
        except ClientError as e:
            logger.error(f"Failed to associate '{collaborator_name}': {e}")
            raise
    
    def disassociate_collaborator(
        self,
        supervisor_agent_id: str,
        collaborator_id: str
    ) -> bool:
        """
        Disassociate collaborator from supervisor
        
        Args:
            supervisor_agent_id: Supervisor agent ID
            collaborator_id: Collaborator agent ID
            
        Returns:
            True if disassociation successful
        """
        try:
            self.client.disassociate_agent_collaborator(
                agentId=supervisor_agent_id,
                agentVersion='DRAFT',
                collaboratorId=collaborator_id
            )
            logger.info(f"Disassociated collaborator: {collaborator_id}")
            return True
            
        except self.client.exceptions.ResourceNotFoundException:
            logger.info(f"Collaborator {collaborator_id} not found")
            return True
        except ClientError as e:
            logger.error(f"Failed to disassociate collaborator: {e}")
            raise
    
    def cleanup_old_collaborators(
        self,
        supervisor_agent_id: str,
        keep_collaborators: Set[str]
    ):
        """
        Remove collaborators not in the keep set
        
        Args:
            supervisor_agent_id: Supervisor agent ID
            keep_collaborators: Set of collaborator names to keep
        """
        try:
            response = self.client.list_agent_collaborators(
                agentId=supervisor_agent_id,
                agentVersion='DRAFT',
                maxResults=10
            )
            
            for collab in response.get('agentCollaboratorSummaries', []):
                if collab['collaboratorName'] not in keep_collaborators:
                    self.disassociate_collaborator(
                        supervisor_agent_id,
                        collab['agentId']
                    )
                    logger.info(f"Removed old collaborator: {collab['collaboratorName']}")
                    
        except ClientError as e:
            logger.error(f"Failed to cleanup collaborators: {e}")
            raise
    
    def invoke_agent(
        self,
        agent_id: str,
        alias_id: str,
        session_id: str,
        input_text: str,
        enable_trace: bool = True
    ) -> str:
        """
        Invoke agent with input text
        
        Args:
            agent_id: Agent ID
            alias_id: Agent alias ID
            session_id: Session ID
            input_text: Input text
            enable_trace: Enable trace output
            
        Returns:
            Agent response text
        """
        try:
            logger.info(f"Invoking agent {agent_id} with alias {alias_id}")
            response = self.runtime_client.invoke_agent(
                agentId=agent_id,
                agentAliasId=alias_id,
                sessionId=session_id,
                inputText=input_text,
                enableTrace=enable_trace
            )
            
            # Process response stream with better error handling
            output_text = ""
            trace_info = []
            
            for event in response['completion']:
                logger.debug(f"Event: {event.keys()}")
                
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        output_text += chunk['bytes'].decode('utf-8')
                
                if 'trace' in event:
                    trace = event['trace']
                    trace_info.append(trace)
                    logger.info(f"Trace: {trace}")
            
            if trace_info:
                logger.info(f"Trace information collected: {len(trace_info)} events")
            
            logger.info(f"Agent invoked successfully, response length: {len(output_text)}")
            return output_text
            
        except Exception as e:
            logger.error(f"Failed to invoke agent: {e}")
            logger.error(f"Agent ID: {agent_id}, Alias ID: {alias_id}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def delete_agent(self, agent_id: str) -> bool:
        """
        Delete agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if deletion successful
        """
        try:
            # Delete all aliases first
            response = self.client.list_agent_aliases(
                agentId=agent_id,
                maxResults=10
            )
            
            for alias in response.get('agentAliasSummaries', []):
                alias_id = alias['agentAliasId']
                # Skip test alias (reserved ID)
                if alias_id == 'TSTALIASID':
                    logger.info(f"Skipping test alias: {alias_id}")
                    continue
                    
                try:
                    self.client.delete_agent_alias(
                        agentId=agent_id,
                        agentAliasId=alias_id
                    )
                    logger.info(f"Deleted alias: {alias_id}")
                except ClientError as e:
                    logger.warning(f"Could not delete alias {alias_id}: {e}")
            
            # Delete agent
            self.client.delete_agent(agentId=agent_id)
            logger.info(f"Deleted agent: {agent_id}")
            
            return True
            
        except self.client.exceptions.ResourceNotFoundException:
            logger.info(f"Agent {agent_id} does not exist")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete agent: {e}")
            raise
    
    def get_agent_by_name(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get agent by name
        
        Args:
            agent_name: Agent name
            
        Returns:
            Agent details or None if not found
        """
        try:
            response = self.client.list_agents(maxResults=100)
            
            for agent in response.get('agentSummaries', []):
                if agent['agentName'] == agent_name:
                    # Get full details
                    agent_response = self.client.get_agent(agentId=agent['agentId'])
                    return agent_response['agent']
            
            return None
            
        except ClientError as e:
            logger.error(f"Failed to get agent by name: {e}")
            return None
    
    def get_action_group_by_name(
        self,
        agent_id: str,
        action_group_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get action group by name
        
        Args:
            agent_id: Agent ID
            action_group_name: Action group name
            
        Returns:
            Action group details or None if not found
        """
        try:
            response = self.client.list_agent_action_groups(
                agentId=agent_id,
                agentVersion='DRAFT',
                maxResults=10
            )
            
            for ag in response.get('actionGroupSummaries', []):
                if ag['actionGroupName'] == action_group_name:
                    return ag
            
            return None
            
        except ClientError as e:
            logger.error(f"Failed to get action group by name: {e}")
            return None
    
    def get_collaborator_by_name(
        self,
        supervisor_agent_id: str,
        collaborator_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get collaborator by name
        
        Args:
            supervisor_agent_id: Supervisor agent ID
            collaborator_name: Collaborator name
            
        Returns:
            Collaborator details or None if not found
        """
        try:
            response = self.client.list_agent_collaborators(
                agentId=supervisor_agent_id,
                agentVersion='DRAFT',
                maxResults=10
            )
            
            for collab in response.get('agentCollaboratorSummaries', []):
                if collab['collaboratorName'] == collaborator_name:
                    return collab
            
            return None
            
        except ClientError as e:
            logger.error(f"Failed to get collaborator by name: {e}")
            return None
    
    def _wait_for_agent_status(
        self,
        agent_id: str,
        target_status: str,
        max_wait_time: int = 300,
        check_interval: int = 5
    ):
        """Wait for agent to reach target status"""
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            try:
                response = self.client.get_agent(agentId=agent_id)
                status = response['agent']['agentStatus']
                
                if status == target_status:
                    return
                elif status == 'FAILED':
                    raise Exception(f"Agent entered FAILED state")
                
                logger.info(f"Agent status: {status}. Waiting for {target_status}...")
                
            except ClientError as e:
                logger.error(f"Error checking agent status: {e}")
                raise
            
            time.sleep(check_interval)
            elapsed_time += check_interval
        
        raise TimeoutError(f"Agent did not reach {target_status} within {max_wait_time} seconds")
    
    def _wait_for_alias_status(
        self,
        agent_id: str,
        alias_id: str,
        target_status: str,
        max_wait_time: int = 300,
        check_interval: int = 5
    ):
        """Wait for alias to reach target status"""
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            try:
                response = self.client.get_agent_alias(
                    agentId=agent_id,
                    agentAliasId=alias_id
                )
                status = response['agentAlias']['agentAliasStatus']
                
                if status == target_status:
                    return
                elif status == 'FAILED':
                    raise Exception(f"Alias entered FAILED state")
                
                logger.info(f"Alias status: {status}. Waiting for {target_status}...")
                
            except ClientError as e:
                logger.error(f"Error checking alias status: {e}")
                raise
            
            time.sleep(check_interval)
            elapsed_time += check_interval
        
        raise TimeoutError(f"Alias did not reach {target_status} within {max_wait_time} seconds")


