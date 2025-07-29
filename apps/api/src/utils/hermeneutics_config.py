"""
Hermeneutics Configuration Loading and Management Utility

Provides loading, validation, and versioning for hermeneutics prompts
used in the AdvancedGeneratorNode for theological AI responses.
"""

import yaml
import logging
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class HermeneuticsConfig:
    """
    Configuration manager for hermeneutics prompts with versioning and validation
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize hermeneutics configuration manager"""
        if config_path is None:
            # Default to config directory relative to this file
            config_dir = Path(__file__).parent.parent / "config"
            config_path = config_dir / "hermeneutics_prompts.yaml"
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load hermeneutics configuration from YAML file"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Hermeneutics config not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"Loaded hermeneutics config v{self.get_version()}")
            
            # Validate configuration
            self._validate_config()
            
        except Exception as e:
            logger.error(f"Failed to load hermeneutics config: {e}")
            # Load fallback minimal config
            self._load_fallback_config()
    
    def _validate_config(self) -> None:
        """Validate hermeneutics configuration structure and content"""
        required_sections = ['version', 'compiled_prompts', 'token_budgets']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required config section: {section}")
        
        # Validate required principles
        validation_rules = self.config.get('validation_rules', {})
        required_principles = validation_rules.get('required_principles', [])
        primary_prompt = self.get_system_prompt()
        
        for principle in required_principles:
            if principle.lower() not in primary_prompt.lower():
                logger.warning(f"Required hermeneutical principle missing: {principle}")
        
        logger.info("Hermeneutics configuration validation passed")
    
    def _load_fallback_config(self) -> None:
        """Load minimal fallback configuration for emergency scenarios"""
        logger.warning("Loading fallback hermeneutics configuration")
        
        self.config = {
            "version": "fallback",
            "compiled_prompts": {
                "primary_v1_0": (
                    "You are an Expert Biblical Scholar applying sound hermeneutical principles. "
                    "Interpret Scripture with Scripture, consider historical-grammatical context, "
                    "maintain Christocentric focus, and ensure canonical consistency. "
                    "Provide scripturally grounded answers with biblical citations."
                )
            },
            "token_budgets": {
                "hermeneutics_section": 400,
                "context_chunks": 2000,
                "user_query": 100,
                "response_budget": 1500,
                "total_budget": 4000
            }
        }
    
    def get_version(self) -> str:
        """Get current hermeneutics configuration version"""
        return self.config.get('version', 'unknown')
    
    def get_system_prompt(self, version: Optional[str] = None) -> str:
        """
        Retrieve hermeneutics system prompt by version
        
        Args:
            version: Specific version to retrieve, or None for current version
            
        Returns:
            Compiled hermeneutics system prompt text
        """
        try:
            compiled_prompts = self.config.get('compiled_prompts', {})
            
            if version is None:
                # Get primary prompt for current version
                prompt_key = f"primary_v{self.get_version()}"
                if prompt_key in compiled_prompts:
                    return compiled_prompts[prompt_key]
                else:
                    # Fallback to first available prompt
                    return list(compiled_prompts.values())[0]
            else:
                # Get specific version
                prompt_key = f"primary_v{version}"
                if prompt_key in compiled_prompts:
                    return compiled_prompts[prompt_key]
                else:
                    raise ValueError(f"Hermeneutics prompt version not found: {version}")
                    
        except Exception as e:
            logger.error(f"Failed to retrieve hermeneutics prompt: {e}")
            # Return minimal fallback prompt
            return (
                "You are an Expert Biblical Scholar. Apply sound hermeneutical principles "
                "and provide scripturally grounded responses with biblical citations."
            )
    
    def get_prompt_variant(self, variant_name: str) -> str:
        """
        Get specific prompt variant (concise, advanced, etc.)
        
        Args:
            variant_name: Name of variant (e.g., 'concise_v1_0', 'advanced_v1_0')
            
        Returns:
            Compiled prompt text for the specified variant
        """
        try:
            variants = self.config.get('prompt_variants', {})
            
            if variant_name in variants:
                return variants[variant_name].get('compiled', '')
            
            # Try compiled_prompts as fallback
            compiled_prompts = self.config.get('compiled_prompts', {})
            if variant_name in compiled_prompts:
                return compiled_prompts[variant_name]
            
            raise ValueError(f"Prompt variant not found: {variant_name}")
            
        except Exception as e:
            logger.error(f"Failed to retrieve prompt variant {variant_name}: {e}")
            return self.get_system_prompt()  # Fallback to primary prompt
    
    def get_token_budget(self, section: str) -> int:
        """
        Get token budget for specific prompt section
        
        Args:
            section: Budget section name (e.g., 'hermeneutics_section', 'total_budget')
            
        Returns:
            Token count budget for the specified section
        """
        budgets = self.config.get('token_budgets', {})
        return budgets.get(section, 0)
    
    def get_composition_settings(self) -> Dict[str, Any]:
        """Get prompt composition settings and formatting options"""
        return self.config.get('composition_settings', {
            'section_separator': '\n\n=== ',
            'subsection_separator': '\n• ',
            'instruction_prefix': '=== INSTRUCTIONS ===\n',
            'default_instructions': (
                'Using the hermeneutical framework above and the provided source material, '
                'provide a comprehensive, biblically grounded response to the user\'s question. '
                'Cite specific biblical references and maintain theological precision.'
            )
        })
    
    def is_ab_testing_enabled(self) -> bool:
        """Check if A/B testing is enabled for hermeneutics prompts"""
        ab_config = self.config.get('ab_testing', {})
        return ab_config.get('enabled', False)
    
    def get_ab_testing_config(self) -> Dict[str, Any]:
        """Get A/B testing configuration for prompt experiments"""
        return self.config.get('ab_testing', {})
    
    def validate_prompt(self, prompt: str) -> bool:
        """
        Validate prompt structure and content against configuration rules
        
        Args:
            prompt: Prompt text to validate
            
        Returns:
            True if prompt passes validation, False otherwise
        """
        try:
            validation_rules = self.config.get('validation_rules', {})
            
            # Check token count limit
            max_tokens = validation_rules.get('max_token_count', 1000)
            estimated_tokens = len(prompt.split()) * 1.3  # Rough estimation
            
            if estimated_tokens > max_tokens:
                logger.warning(f"Prompt exceeds token limit: {estimated_tokens} > {max_tokens}")
                return False
            
            # Check required principles
            required_principles = validation_rules.get('required_principles', [])
            for principle in required_principles:
                if principle.lower() not in prompt.lower():
                    logger.warning(f"Required principle missing from prompt: {principle}")
                    return False
            
            # Check forbidden terms
            forbidden_terms = validation_rules.get('forbidden_terms', [])
            for term in forbidden_terms:
                if term.lower() in prompt.lower():
                    logger.error(f"Forbidden term found in prompt: {term}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Prompt validation failed: {e}")
            return False
    
    def reload_config(self) -> bool:
        """
        Reload configuration from file (for hot-reloading in development)
        
        Returns:
            True if reload successful, False otherwise
        """
        try:
            self._load_config()
            logger.info("Hermeneutics configuration reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to reload hermeneutics configuration: {e}")
            return False
    
    def get_supported_versions(self) -> List[str]:
        """Get list of supported hermeneutics prompt versions"""
        versioning = self.config.get('versioning', {})
        return versioning.get('supported_versions', [self.get_version()])
    
    def get_version_info(self, version: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific version
        
        Args:
            version: Version identifier
            
        Returns:
            Dictionary with version details (date, description, changes, etc.)
        """
        versioning = self.config.get('versioning', {})
        version_history = versioning.get('version_history', [])
        
        for version_info in version_history:
            if version_info.get('version') == version:
                return version_info
        
        return {}