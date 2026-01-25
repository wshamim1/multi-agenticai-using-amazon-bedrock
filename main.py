"""
Main Orchestration Script
Entry point for deploying and managing the Multi-Agent AI System
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from config import config
from orchestrator import MultiAgentOrchestrator
from agents_config import get_enabled_agents

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def deploy_system(
    collaborators: list,
    upload_data: bool = True,
    data_dir: str = "data"
):
    """
    Deploy the complete multi-agent system
    
    Args:
        collaborators: List of collaborator configurations
        upload_data: Whether to upload data to Knowledge Base
        data_dir: Directory containing data to upload
    """
    logger.info("Starting system deployment...")
    
    orchestrator = MultiAgentOrchestrator()
    
    result = orchestrator.deploy_complete_system(
        collaborator_configs=collaborators,
        upload_data_to_kb=upload_data,
        data_directory=data_dir
    )
    
    logger.info("\n" + "=" * 80)
    logger.info("DEPLOYMENT SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Supervisor Agent ID: {result['supervisor_agent_id']}")
    logger.info(f"Knowledge Base ID: {result['knowledge_base_id']}")
    logger.info(f"S3 Bucket: {result['bucket_name']}")
    logger.info(f"OpenSearch Endpoint: {result['collection_endpoint']}")
    logger.info(f"Collaborators: {', '.join(result['collaborators'])}")
    logger.info(f"Deployment Time: {result['deployment_time']:.2f} seconds")
    logger.info("=" * 80)


def cleanup_system():
    """Clean up all deployed resources"""
    logger.info("Starting system cleanup...")
    
    from cleanup import cleanup_all_resources
    
    try:
        cleanup_all_resources()
        logger.info("✅ Cleanup completed successfully")
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        raise


def test_agent(query: str):
    """
    Test the deployed agent with a query
    
    Args:
        query: Test query
    """
    from core.agent_manager import AgentManager
    
    logger.info(f"Testing agent with query: {query}")
    
    agent_mgr = AgentManager(
        config.aws.bedrock_agent_client,
        config.aws.bedrock_agent_runtime_client,
        config.aws.account_id,
        config.aws.region
    )
    
    # Get supervisor agent
    agent = agent_mgr.get_agent_by_name(config.agent.supervisor_agent_name)
    if not agent:
        logger.error("Supervisor agent not found. Please deploy the system first.")
        return
    
    agent_id = agent['agentId']
    
    # Get alias
    aliases = agent_mgr.client.list_agent_aliases(agentId=agent_id, maxResults=1)
    if not aliases.get('agentAliasSummaries'):
        logger.error("No agent alias found. Please prepare the agent first.")
        return
    
    alias_id = aliases['agentAliasSummaries'][0]['agentAliasId']
    
    # Invoke agent
    import uuid
    session_id = str(uuid.uuid4())
    response = agent_mgr.invoke_agent(agent_id, alias_id, session_id, query)
    
    logger.info("\n" + "=" * 80)
    logger.info("AGENT RESPONSE")
    logger.info("=" * 80)
    logger.info(response)
    logger.info("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Multi-Agent AI System - Deployment and Management"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy the complete system')
    deploy_parser.add_argument(
        '--upload-data',
        action='store_true',
        default=True,
        help='Upload data to Knowledge Base (default: True)'
    )
    deploy_parser.add_argument(
        '--no-upload-data',
        action='store_false',
        dest='upload_data',
        help='Skip uploading data to Knowledge Base'
    )
    deploy_parser.add_argument(
        '--data-dir',
        type=str,
        default='data',
        help='Directory containing data to upload (default: data)'
    )
    deploy_parser.add_argument(
        '--disable-weather',
        action='store_true',
        help='Disable Weather collaborator'
    )
    deploy_parser.add_argument(
        '--disable-stock',
        action='store_true',
        help='Disable Stock Market collaborator'
    )
    deploy_parser.add_argument(
        '--disable-news',
        action='store_true',
        help='Disable News collaborator'
    )
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up all resources')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test the deployed agent')
    test_parser.add_argument('query', type=str, help='Test query')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Show configuration')
    
    args = parser.parse_args()
    
    if args.command == 'deploy':
        # Get enabled collaborators from config
        collaborators = get_enabled_agents(
            disable_weather=args.disable_weather,
            disable_stock=args.disable_stock,
            disable_news=args.disable_news
        )
        
        if not collaborators:
            logger.error("At least one collaborator must be enabled")
            sys.exit(1)
        
        deploy_system(
            collaborators=collaborators,
            upload_data=args.upload_data,
            data_dir=args.data_dir
        )
    
    elif args.command == 'cleanup':
        cleanup_system()
    
    elif args.command == 'test':
        test_agent(args.query)
    
    elif args.command == 'config':
        config.print_summary()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

