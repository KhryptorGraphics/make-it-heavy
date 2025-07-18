"""
Custom exception classes for Make It Heavy
Provides structured error handling with context and recovery suggestions.
"""

from typing import Optional, Dict, Any


class MakeItHeavyError(Exception):
    """Base exception class for Make It Heavy errors"""
    
    def __init__(self, message: str, error_code: str = "UNKNOWN", context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
    
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


class APIError(MakeItHeavyError):
    """Exception for OpenRouter API related errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message, "API_ERROR", {"status_code": status_code, "response_data": response_data})
        self.status_code = status_code
        self.response_data = response_data


class ToolExecutionError(MakeItHeavyError):
    """Exception for tool execution errors"""
    
    def __init__(self, tool_name: str, message: str, tool_args: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Tool '{tool_name}' failed: {message}",
            "TOOL_ERROR",
            {"tool_name": tool_name, "tool_args": tool_args}
        )
        self.tool_name = tool_name
        self.tool_args = tool_args


class ConfigurationError(MakeItHeavyError):
    """Exception for configuration related errors"""
    
    def __init__(self, message: str, config_path: Optional[str] = None):
        super().__init__(message, "CONFIG_ERROR", {"config_path": config_path})
        self.config_path = config_path


class AgentError(MakeItHeavyError):
    """Exception for agent execution errors"""
    
    def __init__(self, message: str, agent_id: Optional[str] = None, iteration: Optional[int] = None):
        super().__init__(
            message,
            "AGENT_ERROR",
            {"agent_id": agent_id, "iteration": iteration}
        )
        self.agent_id = agent_id
        self.iteration = iteration


class OrchestrationError(MakeItHeavyError):
    """Exception for orchestration errors"""
    
    def __init__(self, message: str, phase: Optional[str] = None, agent_count: Optional[int] = None):
        super().__init__(
            message,
            "ORCHESTRATION_ERROR",
            {"phase": phase, "agent_count": agent_count}
        )
        self.phase = phase
        self.agent_count = agent_count


class RetryableError(MakeItHeavyError):
    """Exception for errors that can be retried"""
    
    def __init__(self, message: str, retry_count: int = 0, max_retries: int = 3):
        super().__init__(
            message,
            "RETRYABLE_ERROR",
            {"retry_count": retry_count, "max_retries": max_retries}
        )
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.can_retry = retry_count < max_retries


class ValidationError(MakeItHeavyError):
    """Exception for input validation errors"""
    
    def __init__(self, message: str, field_name: Optional[str] = None, field_value: Optional[Any] = None):
        super().__init__(
            message,
            "VALIDATION_ERROR",
            {"field_name": field_name, "field_value": field_value}
        )
        self.field_name = field_name
        self.field_value = field_value