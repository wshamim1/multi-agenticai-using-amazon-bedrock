"""
Model Configuration Loader
Loads and manages model configurations from YAML file
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Model configuration data class"""
    id: str
    name: str
    description: str
    max_tokens: int
    temperature: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }


class ModelConfigLoader:
    """Loads and manages model configurations"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize model config loader
        
        Args:
            config_path: Path to models_config.yaml file
        """
        if config_path is None:
            # Default to models_config.yaml in hackathon directory
            config_path = Path(__file__).parent.parent / "models_config.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded model configuration from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Model config file not found: {self.config_path}")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading model config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file not found"""
        return {
            'agent_models': {
                'primary': {
                    'id': 'anthropic.claude-3-sonnet-20240229-v1:0',
                    'name': 'Claude 3 Sonnet',
                    'description': 'Default model',
                    'max_tokens': 4096,
                    'temperature': 0.7
                }
            },
            'embedding_models': {
                'primary': {
                    'id': 'amazon.titan-embed-text-v1',
                    'name': 'Titan Embeddings',
                    'description': 'Default embeddings',
                    'dimensions': 1536
                }
            }
        }
    
    def get_agent_model(self, model_type: str = 'primary') -> ModelConfig:
        """
        Get agent model configuration
        
        Args:
            model_type: Type of model ('primary' or alternative index)
            
        Returns:
            ModelConfig object
        """
        try:
            if model_type == 'primary':
                model_data = self.config['agent_models']['primary']
            else:
                # Get from alternatives
                alternatives = self.config['agent_models'].get('alternatives', [])
                model_data = alternatives[int(model_type)] if model_type.isdigit() else alternatives[0]
            
            return ModelConfig(
                id=model_data['id'],
                name=model_data['name'],
                description=model_data['description'],
                max_tokens=model_data['max_tokens'],
                temperature=model_data['temperature']
            )
        except Exception as e:
            logger.error(f"Error getting agent model: {e}")
            return self._get_default_agent_model()
    
    def get_embedding_model(self, model_type: str = 'primary') -> Dict[str, Any]:
        """
        Get embedding model configuration
        
        Args:
            model_type: Type of model ('primary' or alternative index)
            
        Returns:
            Model configuration dictionary
        """
        try:
            if model_type == 'primary':
                return self.config['embedding_models']['primary']
            else:
                alternatives = self.config['embedding_models'].get('alternatives', [])
                return alternatives[int(model_type)] if model_type.isdigit() else alternatives[0]
        except Exception as e:
            logger.error(f"Error getting embedding model: {e}")
            return self.config['embedding_models']['primary']
    
    def get_text_generation_model(self, model_type: str = 'primary') -> ModelConfig:
        """
        Get text generation model configuration
        
        Args:
            model_type: Type of model ('primary' or alternative index)
            
        Returns:
            ModelConfig object
        """
        try:
            if model_type == 'primary':
                model_data = self.config['text_generation_models']['primary']
            else:
                alternatives = self.config['text_generation_models'].get('alternatives', [])
                model_data = alternatives[int(model_type)] if model_type.isdigit() else alternatives[0]
            
            return ModelConfig(
                id=model_data['id'],
                name=model_data['name'],
                description=model_data['description'],
                max_tokens=model_data['max_tokens'],
                temperature=model_data['temperature']
            )
        except Exception as e:
            logger.error(f"Error getting text generation model: {e}")
            return self._get_default_agent_model()
    
    def get_image_generation_model(self, model_type: str = 'primary') -> Dict[str, Any]:
        """
        Get image generation model configuration
        
        Args:
            model_type: Type of model ('primary' or alternative index)
            
        Returns:
            Model configuration dictionary
        """
        try:
            if model_type == 'primary':
                return self.config['image_generation_models']['primary']
            else:
                alternatives = self.config['image_generation_models'].get('alternatives', [])
                return alternatives[int(model_type)] if model_type.isdigit() else alternatives[0]
        except Exception as e:
            logger.error(f"Error getting image generation model: {e}")
            return self.config['image_generation_models']['primary']
    
    def get_use_case_model(self, use_case: str) -> Dict[str, Any]:
        """
        Get model configuration for specific use case
        
        Args:
            use_case: Use case name (e.g., 'etl_operations', 'document_analysis')
            
        Returns:
            Model configuration dictionary
        """
        try:
            return self.config['use_case_models'].get(use_case, {})
        except Exception as e:
            logger.error(f"Error getting use case model: {e}")
            return {}
    
    def get_model_parameters(self, parameter_type: str) -> Dict[str, Any]:
        """
        Get model parameters for specific type
        
        Args:
            parameter_type: Type of parameters (e.g., 'agent', 'text_generation')
            
        Returns:
            Parameters dictionary
        """
        try:
            return self.config['model_parameters'].get(parameter_type, {})
        except Exception as e:
            logger.error(f"Error getting model parameters: {e}")
            return {}
    
    def get_fallback_models(self) -> List[str]:
        """
        Get list of fallback models
        
        Returns:
            List of model IDs
        """
        try:
            return self.config['model_selection']['fallback_order']
        except Exception as e:
            logger.error(f"Error getting fallback models: {e}")
            return ['anthropic.claude-3-sonnet-20240229-v1:0']
    
    def is_model_available_in_region(self, model_id: str, region: str) -> bool:
        """
        Check if model is available in specific region
        
        Args:
            model_id: Model ID
            region: AWS region
            
        Returns:
            True if available, False otherwise
        """
        try:
            available_models = self.config['regional_availability'].get(region, [])
            return model_id in available_models
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return True  # Assume available if check fails
    
    def get_model_capabilities(self, model_id: str) -> Dict[str, str]:
        """
        Get capabilities for specific model
        
        Args:
            model_id: Model ID
            
        Returns:
            Capabilities dictionary
        """
        try:
            return self.config['model_capabilities'].get(model_id, {})
        except Exception as e:
            logger.error(f"Error getting model capabilities: {e}")
            return {}
    
    def get_cost_optimized_model(self, task_complexity: str = 'simple') -> str:
        """
        Get cost-optimized model based on task complexity
        
        Args:
            task_complexity: 'simple' or 'complex'
            
        Returns:
            Model ID
        """
        try:
            cost_config = self.config['cost_optimization']
            if task_complexity == 'simple':
                return cost_config['simple_tasks_model']
            else:
                return cost_config['complex_tasks_model']
        except Exception as e:
            logger.error(f"Error getting cost-optimized model: {e}")
            return 'anthropic.claude-3-sonnet-20240229-v1:0'
    
    def _get_default_agent_model(self) -> ModelConfig:
        """Get default agent model"""
        return ModelConfig(
            id='anthropic.claude-3-sonnet-20240229-v1:0',
            name='Claude 3 Sonnet',
            description='Default model',
            max_tokens=4096,
            temperature=0.7
        )
    
    def list_all_models(self) -> Dict[str, List[str]]:
        """
        List all available models by category
        
        Returns:
            Dictionary of model categories and their model IDs
        """
        models = {
            'agent_models': [],
            'text_generation_models': [],
            'embedding_models': [],
            'image_generation_models': []
        }
        
        try:
            # Agent models
            models['agent_models'].append(self.config['agent_models']['primary']['id'])
            models['agent_models'].extend([m['id'] for m in self.config['agent_models'].get('alternatives', [])])
            
            # Text generation models
            models['text_generation_models'].append(self.config['text_generation_models']['primary']['id'])
            models['text_generation_models'].extend([m['id'] for m in self.config['text_generation_models'].get('alternatives', [])])
            
            # Embedding models
            models['embedding_models'].append(self.config['embedding_models']['primary']['id'])
            models['embedding_models'].extend([m['id'] for m in self.config['embedding_models'].get('alternatives', [])])
            
            # Image generation models
            models['image_generation_models'].append(self.config['image_generation_models']['primary']['id'])
            models['image_generation_models'].extend([m['id'] for m in self.config['image_generation_models'].get('alternatives', [])])
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
        
        return models
    
    def reload_config(self):
        """Reload configuration from file"""
        self.config = self._load_config()
        logger.info("Model configuration reloaded")


# Global instance
_model_config_loader = None


def get_model_config_loader() -> ModelConfigLoader:
    """
    Get global model config loader instance
    
    Returns:
        ModelConfigLoader instance
    """
    global _model_config_loader
    if _model_config_loader is None:
        _model_config_loader = ModelConfigLoader()
    return _model_config_loader


if __name__ == "__main__":
    # Test the loader
    loader = ModelConfigLoader()
    
    print("Agent Model:", loader.get_agent_model().to_dict())
    print("\nEmbedding Model:", loader.get_embedding_model())
    print("\nText Generation Model:", loader.get_text_generation_model().to_dict())
    print("\nImage Generation Model:", loader.get_image_generation_model())
    print("\nETL Operations Model:", loader.get_use_case_model('etl_operations'))
    print("\nAll Models:", loader.list_all_models())

