"""
Global test configuration and fixtures for Make It Heavy test suite.
"""

import pytest
import tempfile
import yaml
import os
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any

from utils import load_config
from exceptions import ConfigurationError


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Provide test configuration for all tests."""
    return {
        'openrouter': {
            'api_key': 'sk-test-key-12345',
            'base_url': 'https://openrouter.ai/api/v1',
            'model': 'test/model'
        },
        'agent': {
            'max_iterations': 3  # Faster tests
        },
        'orchestrator': {
            'parallel_agents': 2,  # Faster tests
            'task_timeout': 10,  # Faster tests
            'aggregation_strategy': 'consensus',
            'question_generation_prompt': 'Generate {num_agents} questions: {user_input}',
            'synthesis_prompt': 'Synthesize: {agent_responses}'
        },
        'search': {
            'max_results': 3,
            'user_agent': 'Test Agent'
        },
        'ui': {
            'rich_output': False,  # Disable for tests
            'show_progress': False,
            'show_metrics': False,
            'show_timeline': False,
            'silent_mode': True
        },
        'logging': {
            'enabled': False  # Disable for tests
        },
        'performance': {
            'max_concurrent_agents': 2,
            'api_timeout': 5,  # Faster timeout for tests
            'retry_failed_calls': False,
            'max_retries': 1
        }
    }


@pytest.fixture
def temp_config_file(test_config: Dict[str, Any]) -> str:
    """Create temporary config file for tests."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_config, f)
        return f.name


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for API tests."""
    with patch('agent.OpenAI') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].message.tool_calls = None
        
        mock_client.chat.completions.create.return_value = mock_response
        
        yield mock_client


@pytest.fixture
def mock_ui_manager():
    """Mock UI manager for tests."""
    mock_ui = Mock()
    mock_ui.create_agent_metrics.return_value = Mock()
    mock_ui.update_agent_status = Mock()
    mock_ui.log_timeline = Mock()
    mock_ui.log_api_call = Mock()
    mock_ui.log_error = Mock()
    mock_ui.update_orchestrator_phase = Mock()
    mock_ui.set_questions_generated = Mock()
    mock_ui.agent_completed = Mock()
    mock_ui.agent_failed = Mock()
    mock_ui.update_synthesis_progress = Mock()
    return mock_ui


@pytest.fixture
def sample_user_input() -> str:
    """Standard test user input."""
    return "What is artificial intelligence?"


@pytest.fixture
def sample_tool_response() -> Dict[str, Any]:
    """Sample tool execution response."""
    return {
        "success": True,
        "result": "Tool executed successfully",
        "execution_time": 0.1
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ['TESTING'] = '1'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_tools():
    """Mock tools for agent testing."""
    return [
        {
            "type": "function",
            "function": {
                "name": "test_tool",
                "description": "A test tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string", "description": "Test input"}
                    },
                    "required": ["input"]
                }
            }
        }
    ]


@pytest.fixture
def clean_test_files():
    """Clean up test files after test."""
    test_files = []
    
    def add_file(filename: str):
        test_files.append(filename)
    
    yield add_file
    
    # Cleanup
    for filename in test_files:
        try:
            Path(filename).unlink(missing_ok=True)
        except:
            pass


# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on path."""
    for item in items:
        # Add markers based on test file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)