"""
Unit tests for OpenRouterAgent class.
Tests agent initialization, LLM calls, tool execution, and agentic loop.
"""

import pytest
import yaml
from unittest.mock import Mock, patch, MagicMock
from openai.types.chat import ChatCompletion

from agent import OpenRouterAgent
from exceptions import APIError, ToolExecutionError, AgentError, ConfigurationError
from constants import AGENT_STATUS_RUNNING, ERROR_INVALID_API_KEY


class TestOpenRouterAgent:
    """Test suite for OpenRouterAgent class."""

    def test_agent_initialization_success(self, temp_config_file, mock_ui_manager):
        """Test successful agent initialization."""
        with patch('agent.discover_tools') as mock_discover:
            mock_discover.return_value = {}
            
            agent = OpenRouterAgent(
                config_path=temp_config_file,
                ui_manager=mock_ui_manager,
                agent_id="test_agent"
            )
            
            assert agent.agent_id == "test_agent"
            assert agent.ui_manager == mock_ui_manager
            assert agent.config is not None
            assert agent.client is not None

    def test_agent_initialization_missing_config(self):
        """Test agent initialization with missing config file."""
        with pytest.raises(FileNotFoundError):
            OpenRouterAgent(config_path="nonexistent.yaml")

    def test_agent_initialization_invalid_config(self, tmp_path):
        """Test agent initialization with invalid config."""
        invalid_config = tmp_path / "invalid.yaml"
        invalid_config.write_text("invalid: yaml: content:")
        
        with pytest.raises(yaml.YAMLError):
            OpenRouterAgent(config_path=str(invalid_config))

    @patch('agent.discover_tools')
    def test_call_llm_success(self, mock_discover, temp_config_file, mock_openai_client):
        """Test successful LLM API call."""
        mock_discover.return_value = {}
        
        agent = OpenRouterAgent(config_path=temp_config_file)
        messages = [{"role": "user", "content": "test message"}]
        
        response = agent.call_llm(messages)
        
        assert response is not None
        mock_openai_client.chat.completions.create.assert_called_once()

    @patch('agent.discover_tools')
    def test_call_llm_api_error(self, mock_discover, temp_config_file):
        """Test LLM API call with error."""
        mock_discover.return_value = {}
        
        with patch('agent.OpenAI') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            
            agent = OpenRouterAgent(config_path=temp_config_file)
            messages = [{"role": "user", "content": "test"}]
            
            with pytest.raises(APIError):
                agent.call_llm(messages)

    @patch('agent.discover_tools')
    def test_call_llm_unauthorized(self, mock_discover, temp_config_file):
        """Test LLM API call with 401 unauthorized."""
        mock_discover.return_value = {}
        
        with patch('agent.OpenAI') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("401 unauthorized")
            
            agent = OpenRouterAgent(config_path=temp_config_file)
            messages = [{"role": "user", "content": "test"}]
            
            with pytest.raises(APIError) as exc_info:
                agent.call_llm(messages)
            assert exc_info.value.status_code == 401

    @patch('agent.discover_tools')
    def test_handle_tool_call_success(self, mock_discover, temp_config_file):
        """Test successful tool execution."""
        # Mock tool
        mock_tool = Mock()
        mock_tool.return_value = {"success": True, "result": "Tool executed"}
        mock_discover.return_value = {"test_tool": Mock()}
        
        agent = OpenRouterAgent(config_path=temp_config_file)
        agent.tool_mapping = {"test_tool": mock_tool}
        
        # Mock tool call
        tool_call = Mock()
        tool_call.function.name = "test_tool"
        tool_call.function.arguments = '{"input": "test"}'
        tool_call.id = "call_123"
        
        result = agent.handle_tool_call(tool_call)
        
        assert result["role"] == "tool"
        assert result["tool_call_id"] == "call_123"
        mock_tool.assert_called_once()

    @patch('agent.discover_tools')
    def test_handle_tool_call_invalid_tool(self, mock_discover, temp_config_file):
        """Test tool execution with invalid tool name."""
        mock_discover.return_value = {}
        
        agent = OpenRouterAgent(config_path=temp_config_file)
        agent.tool_mapping = {}
        
        # Mock tool call
        tool_call = Mock()
        tool_call.function.name = "nonexistent_tool"
        tool_call.function.arguments = '{"input": "test"}'
        tool_call.id = "call_123"
        
        with pytest.raises(ToolExecutionError):
            agent.handle_tool_call(tool_call)

    @patch('agent.discover_tools')
    def test_handle_tool_call_invalid_arguments(self, mock_discover, temp_config_file):
        """Test tool execution with invalid JSON arguments."""
        mock_tool = Mock()
        mock_discover.return_value = {"test_tool": Mock()}
        
        agent = OpenRouterAgent(config_path=temp_config_file)
        agent.tool_mapping = {"test_tool": mock_tool}
        
        # Mock tool call with invalid JSON
        tool_call = Mock()
        tool_call.function.name = "test_tool"
        tool_call.function.arguments = 'invalid json'
        tool_call.id = "call_123"
        
        with pytest.raises(ToolExecutionError):
            agent.handle_tool_call(tool_call)

    @patch('agent.discover_tools')
    def test_run_with_completion(self, mock_discover, temp_config_file, mock_ui_manager):
        """Test agent run with task completion."""
        mock_discover.return_value = {}
        
        with patch('agent.OpenAI') as mock_client_class:
            # Mock completion response
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # First response with tool call
            mock_response1 = Mock()
            mock_response1.choices = [Mock()]
            mock_response1.choices[0].message = Mock()
            mock_response1.choices[0].message.content = None
            mock_response1.choices[0].message.tool_calls = [Mock()]
            mock_response1.choices[0].message.tool_calls[0].function.name = "mark_task_complete"
            mock_response1.choices[0].message.tool_calls[0].function.arguments = '{"summary": "Task done"}'
            mock_response1.choices[0].message.tool_calls[0].id = "call_123"
            
            mock_client.chat.completions.create.return_value = mock_response1
            
            agent = OpenRouterAgent(
                config_path=temp_config_file,
                ui_manager=mock_ui_manager,
                agent_id="test_agent"
            )
            
            # Mock mark_task_complete tool
            agent.tool_mapping = {
                "mark_task_complete": lambda **kwargs: {"success": True, "summary": kwargs.get("summary", "")}
            }
            
            result = agent.run("Test input")
            
            assert isinstance(result, str)
            mock_ui_manager.update_agent_status.assert_called()

    @patch('agent.discover_tools')
    def test_run_max_iterations_reached(self, mock_discover, temp_config_file):
        """Test agent run reaching max iterations without completion."""
        mock_discover.return_value = {}
        
        with patch('agent.OpenAI') as mock_client_class:
            # Mock client that never completes
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "Continuing work..."
            mock_response.choices[0].message.tool_calls = None
            
            mock_client.chat.completions.create.return_value = mock_response
            
            agent = OpenRouterAgent(config_path=temp_config_file)
            
            with pytest.raises(AgentError) as exc_info:
                agent.run("Test input")
            
            assert "maximum iterations" in str(exc_info.value).lower()

    @patch('agent.discover_tools')
    def test_update_iteration_progress(self, mock_discover, temp_config_file, mock_ui_manager):
        """Test iteration progress updates."""
        mock_discover.return_value = {}
        
        agent = OpenRouterAgent(
            config_path=temp_config_file,
            ui_manager=mock_ui_manager,
            agent_id="test_agent"
        )
        
        agent._update_iteration_progress(2, 10)
        
        mock_ui_manager.update_agent_iteration.assert_called_with("test_agent", 2)

    @patch('agent.discover_tools')
    def test_initialize_conversation(self, mock_discover, temp_config_file):
        """Test conversation initialization."""
        mock_discover.return_value = {}
        
        agent = OpenRouterAgent(config_path=temp_config_file)
        
        messages = agent._initialize_conversation("Test user input")
        
        assert len(messages) == 2  # system + user
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Test user input"

    @patch('agent.discover_tools')
    def test_handle_assistant_response_content_only(self, mock_discover, temp_config_file):
        """Test handling assistant response with content only."""
        mock_discover.return_value = {}
        
        agent = OpenRouterAgent(config_path=temp_config_file)
        
        mock_message = Mock()
        mock_message.content = "Test response"
        mock_message.tool_calls = None
        
        full_response = []
        result = agent._handle_assistant_response(mock_message, full_response)
        
        assert result is False  # Not completed
        assert "Test response" in full_response

    @patch('agent.discover_tools')  
    def test_handle_assistant_response_with_tool_calls(self, mock_discover, temp_config_file):
        """Test handling assistant response with tool calls."""
        mock_discover.return_value = {}
        
        agent = OpenRouterAgent(config_path=temp_config_file)
        
        # Mock tool call
        mock_tool_call = Mock()
        mock_tool_call.function.name = "test_tool"
        mock_tool_call.function.arguments = '{"input": "test"}'
        mock_tool_call.id = "call_123"
        
        mock_message = Mock()
        mock_message.content = "Using tool..."
        mock_message.tool_calls = [mock_tool_call]
        
        # Mock tool execution
        agent.tool_mapping = {
            "test_tool": lambda **kwargs: {"success": True, "result": "Tool result"}
        }
        
        full_response = []
        with patch.object(agent, 'handle_tool_call') as mock_handle:
            mock_handle.return_value = {"role": "tool", "content": "Tool result"}
            
            result = agent._handle_assistant_response(mock_message, full_response)
            
            assert result is False  # Not completed
            mock_handle.assert_called_once()


@pytest.mark.integration
class TestAgentIntegration:
    """Integration tests for agent with real components."""
    
    @patch('agent.discover_tools')
    def test_agent_with_calculator_tool(self, mock_discover, temp_config_file):
        """Test agent integration with calculator tool."""
        # Mock calculator tool
        calc_tool = Mock()
        calc_tool.to_openrouter_schema.return_value = {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Perform calculation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"}
                    }
                }
            }
        }
        calc_tool.execute.return_value = {"result": "42"}
        
        mock_discover.return_value = {"calculate": calc_tool}
        
        with patch('agent.OpenAI') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock response with calculation
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.content = "The answer is 42"
            mock_response.choices[0].message.tool_calls = None
            
            mock_client.chat.completions.create.return_value = mock_response
            
            agent = OpenRouterAgent(config_path=temp_config_file)
            
            assert "calculate" in agent.tool_mapping
            assert len(agent.tools) == 1