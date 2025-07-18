"""
Centralized logging utility for Make It Heavy
Provides structured logging with configurable output and formatting.
"""

import logging
import sys
from typing import Optional, Dict, Any
from datetime import datetime
from constants import (
    LOG_LEVEL_DEBUG, LOG_LEVEL_INFO, LOG_LEVEL_WARNING, LOG_LEVEL_ERROR
)


class MakeItHeavyLogger:
    """Centralized logger for Make It Heavy application."""
    
    _instances: Dict[str, logging.Logger] = {}
    _configured = False
    
    @classmethod
    def get_logger(cls, name: str = "make_it_heavy") -> logging.Logger:
        """Get or create a logger instance.
        
        Args:
            name: Logger name, defaults to "make_it_heavy"
            
        Returns:
            logging.Logger: Configured logger instance
        """
        if name not in cls._instances:
            cls._instances[name] = cls._create_logger(name)
        return cls._instances[name]
    
    @classmethod
    def configure(cls, config: Optional[Dict[str, Any]] = None) -> None:
        """Configure logging based on application configuration.
        
        Args:
            config: Logging configuration dictionary
        """
        if cls._configured:
            return
            
        # Default configuration
        default_config = {
            "enabled": True,
            "level": LOG_LEVEL_INFO,
            "log_to_file": False,
            "log_file_path": "make_it_heavy.log",
            "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "include_timestamps": True,
            "log_api_calls": False
        }
        
        # Merge with provided config
        if config:
            default_config.update(config)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, default_config["level"]))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        if default_config["enabled"]:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, default_config["level"]))
            
            # Formatter
            formatter = logging.Formatter(default_config["log_format"])
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
            
            # File handler if enabled
            if default_config["log_to_file"]:
                file_handler = logging.FileHandler(default_config["log_file_path"])
                file_handler.setLevel(getattr(logging, default_config["level"]))
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
        
        cls._configured = True
    
    @classmethod
    def _create_logger(cls, name: str) -> logging.Logger:
        """Create a new logger instance.
        
        Args:
            name: Logger name
            
        Returns:
            logging.Logger: New logger instance
        """
        logger = logging.getLogger(name)
        
        # Ensure configuration is applied
        if not cls._configured:
            cls.configure()
            
        return logger


def log_agent_event(agent_id: str, event: str, details: str = "", level: str = LOG_LEVEL_INFO) -> None:
    """Log an agent-related event.
    
    Args:
        agent_id: Agent identifier
        event: Event description
        details: Additional details
        level: Log level
    """
    logger = MakeItHeavyLogger.get_logger(f"agent.{agent_id}")
    log_level = getattr(logging, level)
    logger.log(log_level, f"{event}: {details}")


def log_orchestrator_event(event: str, details: str = "", level: str = LOG_LEVEL_INFO) -> None:
    """Log an orchestrator-related event.
    
    Args:
        event: Event description
        details: Additional details
        level: Log level
    """
    logger = MakeItHeavyLogger.get_logger("orchestrator")
    log_level = getattr(logging, level)
    logger.log(log_level, f"{event}: {details}")


def log_tool_execution(tool_name: str, agent_id: str, success: bool, details: str = "") -> None:
    """Log tool execution event.
    
    Args:
        tool_name: Name of the tool
        agent_id: Agent identifier
        success: Whether execution was successful
        details: Additional details
    """
    logger = MakeItHeavyLogger.get_logger(f"tool.{tool_name}")
    level = LOG_LEVEL_INFO if success else LOG_LEVEL_ERROR
    status = "SUCCESS" if success else "FAILED"
    logger.log(getattr(logging, level), f"Agent {agent_id} - {status}: {details}")


def log_api_call(endpoint: str, agent_id: str, duration: float, success: bool, details: str = "") -> None:
    """Log API call event.
    
    Args:
        endpoint: API endpoint
        agent_id: Agent identifier
        duration: Call duration in seconds
        success: Whether call was successful
        details: Additional details
    """
    logger = MakeItHeavyLogger.get_logger("api")
    level = LOG_LEVEL_INFO if success else LOG_LEVEL_ERROR
    status = "SUCCESS" if success else "FAILED"
    logger.log(getattr(logging, level), 
              f"Agent {agent_id} - {endpoint} - {status} - {duration:.2f}s: {details}")


def log_error(component: str, error: Exception, context: Dict[str, Any] = None) -> None:
    """Log error with context.
    
    Args:
        component: Component name where error occurred
        error: Exception instance
        context: Additional context information
    """
    logger = MakeItHeavyLogger.get_logger(f"error.{component}")
    context_str = f" | Context: {context}" if context else ""
    logger.error(f"{type(error).__name__}: {str(error)}{context_str}", exc_info=True)


def log_performance_metric(component: str, metric_name: str, value: float, unit: str = "") -> None:
    """Log performance metric.
    
    Args:
        component: Component name
        metric_name: Metric name
        value: Metric value
        unit: Unit of measurement
    """
    logger = MakeItHeavyLogger.get_logger(f"metrics.{component}")
    unit_str = f" {unit}" if unit else ""
    logger.info(f"{metric_name}: {value}{unit_str}")


# Initialize default logger
default_logger = MakeItHeavyLogger.get_logger()