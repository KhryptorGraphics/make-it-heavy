"""
Utility functions for Make It Heavy
Centralized common operations to reduce code duplication.
"""

import yaml
import json
import time
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from exceptions import ConfigurationError, ValidationError
from constants import (
    DEFAULT_CONFIG_PATH, DEFAULT_FILE_ENCODING, TOKEN_ESTIMATION_RATIO,
    ERROR_INVALID_CONFIG
)


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load and validate configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dict[str, Any]: Parsed configuration
        
    Raises:
        ConfigurationError: If configuration file is invalid or missing
    """
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}", config_path)
        
        with open(config_path, 'r', encoding=DEFAULT_FILE_ENCODING) as f:
            config = yaml.safe_load(f)
        
        # Validate required sections
        required_sections = ['openrouter', 'agent', 'orchestrator']
        for section in required_sections:
            if section not in config:
                raise ConfigurationError(f"Missing required section '{section}' in config", config_path)
        
        return config
        
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML format: {str(e)}", config_path)
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration: {str(e)}", config_path)


def validate_api_key(api_key: str) -> bool:
    """Validate OpenRouter API key format.
    
    Args:
        api_key: API key to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    if not api_key or api_key.strip() == "":
        return False
    
    # Check for placeholder values
    placeholder_values = ["YOUR KEY", "YOUR_KEY", "REPLACE_ME", ""]
    if api_key.strip() in placeholder_values:
        return False
    
    # Basic format validation (OpenRouter keys typically start with 'sk-')
    if not api_key.startswith('sk-'):
        return False
    
    # Minimum length check
    if len(api_key) < 20:
        return False
    
    return True


def estimate_tokens(text: str) -> int:
    """Estimate token count for text.
    
    Args:
        text: Text to estimate tokens for
        
    Returns:
        int: Estimated token count
    """
    if not text:
        return 0
    
    # Use defined ratio for consistent estimation
    return len(text) // TOKEN_ESTIMATION_RATIO


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if seconds < 1:
        return f"{seconds:.2f}s"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def safe_json_parse(text: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """Safely parse JSON text with error handling.
    
    Args:
        text: JSON text to parse
        
    Returns:
        Parsed JSON object or None if parsing fails
    """
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return None


def validate_input_string(value: str, field_name: str, min_length: int = 1, max_length: int = 10000) -> None:
    """Validate input string with length constraints.
    
    Args:
        value: String to validate
        field_name: Name of the field for error messages
        min_length: Minimum required length
        max_length: Maximum allowed length
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field_name, value)
    
    if len(value) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters", field_name, value)
    
    if len(value) > max_length:
        raise ValidationError(f"{field_name} must be at most {max_length} characters", field_name, value)


def validate_positive_integer(value: int, field_name: str, min_value: int = 1) -> None:
    """Validate positive integer value.
    
    Args:
        value: Integer to validate
        field_name: Name of the field for error messages
        min_value: Minimum allowed value
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, int):
        raise ValidationError(f"{field_name} must be an integer", field_name, value)
    
    if value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}", field_name, value)


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0):
    """Retry function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay between retries
        backoff_factor: Multiplier for delay on each retry
        
    Returns:
        Function result if successful
        
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                delay = base_delay * (backoff_factor ** attempt)
                time.sleep(delay)
    
    # If we get here, all retries failed
    raise last_exception


def create_safe_filename(text: str, max_length: int = 255) -> str:
    """Create a safe filename from text.
    
    Args:
        text: Text to convert to filename
        max_length: Maximum filename length
        
    Returns:
        str: Safe filename
    """
    # Remove or replace unsafe characters
    safe_chars = []
    for char in text:
        if char.isalnum() or char in '-_. ':
            safe_chars.append(char)
        else:
            safe_chars.append('_')
    
    # Join and clean up
    filename = ''.join(safe_chars)
    filename = filename.replace(' ', '_')
    filename = filename.strip('_')
    
    # Truncate if too long
    if len(filename) > max_length:
        filename = filename[:max_length]
    
    return filename


def merge_dictionaries(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dictionaries recursively.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Dict[str, Any]: Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dictionaries(result[key], value)
        else:
            result[key] = value
    
    return result


def get_nested_value(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """Get value from nested dictionary using dot notation.
    
    Args:
        data: Dictionary to search
        key_path: Dot-separated key path (e.g., "openrouter.model")
        default: Default value if key not found
        
    Returns:
        Any: Value at key path or default
    """
    keys = key_path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def set_nested_value(data: Dict[str, Any], key_path: str, value: Any) -> None:
    """Set value in nested dictionary using dot notation.
    
    Args:
        data: Dictionary to modify
        key_path: Dot-separated key path
        value: Value to set
    """
    keys = key_path.split('.')
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value