"""
Integration tests for agent-orchestrator workflows.
Tests complete multi-agent orchestration scenarios.
"""

import pytest
import yaml
import tempfile
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import Future

from agent import OpenRouterAgent
from orchestrator import TaskOrchestrator
from ui_manager import UIManager
from exceptions import APIError, OrchestrationError


@pytest.mark.integration
class TestAgentOrchestratorIntegration:
    """Integration tests for agent and orchestrator working together."""

    @patch('orchestrator.OpenRouterAgent')
    @patch('agent.discover_tools')
    def test_full_orchestration_workflow(self, mock_discover_tools, mock_agent_class, 
                                       temp_config_file, mock_ui_manager):
        """Test complete orchestration workflow with multiple agents."""
        # Mock tool discovery
        mock_discover_tools.return_value = {
            "mock_tool": Mock(execute=lambda **kwargs: {"result": "tool executed"})
        }
        
        # Create mock agents for different stages
        question_agent = Mock()
        question_agent.run.return_value = '["What is AI?", "How does ML work?"]'
        
        working_agent1 = Mock()
        working_agent1.run.return_value = "AI is artificial intelligence technology"
        
        working_agent2 = Mock()
        working_agent2.run.return_value = "ML is machine learning algorithms"
        
        synthesis_agent = Mock()
        synthesis_agent.run.return_value = "AI and ML are complementary technologies"
        
        # Configure mock to return different agents in sequence
        mock_agent_class.side_effect = [
            question_agent,    # For question generation
            working_agent1,    # For first parallel agent
            working_agent2,    # For second parallel agent
            synthesis_agent    # For synthesis
        ]
        
        # Create orchestrator
        orchestrator = TaskOrchestrator(
            config_path=temp_config_file,
            ui_manager=mock_ui_manager
        )
        
        # Mock ThreadPoolExecutor for controlled parallel execution
        with patch('orchestrator.ThreadPoolExecutor') as mock_executor_class:
            mock_executor = Mock()
            mock_executor_class.return_value.__enter__.return_value = mock_executor
            
            # Create mock futures
            future1 = Mock()
            future1.result.return_value = {
                "agent_id": 0,
                "status": "completed", 
                "response": "AI response",
                "execution_time": 1.0
            }
            
            future2 = Mock()
            future2.result.return_value = {
                "agent_id": 1,
                "status": "completed",
                "response": "ML response", 
                "execution_time": 1.2
            }
            
            mock_executor.submit.side_effect = [future1, future2]
            
            # Mock as_completed
            with patch('orchestrator.as_completed') as mock_as_completed:
                mock_as_completed.return_value = [future1, future2]
                
                # Execute orchestration
                result = orchestrator.orchestrate("Tell me about AI and ML")
                
                # Verify result
                assert result == "AI and ML are complementary technologies"
                
                # Verify workflow progression
                mock_ui_manager.update_orchestrator_phase.assert_called()
                mock_ui_manager.set_questions_generated.assert_called()

    @patch('agent.discover_tools')
    def test_agent_tool_integration(self, mock_discover_tools, temp_config_file):
        """Test agent integration with real tool execution."""
        # Mock a calculator tool
        calc_tool = Mock()
        calc_tool.to_openrouter_schema.return_value = {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Perform calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"}
                    }
                }
            }
        }
        calc_tool.execute.return_value = {"result": 42, "expression": "6*7"}
        
        mock_discover_tools.return_value = {"calculate": calc_tool}
        
        with patch('agent.OpenAI') as mock_openai:
            # Mock OpenAI client
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # First response: Agent decides to use calculator
            tool_call_response = Mock()
            tool_call_response.choices = [Mock()]
            tool_call_response.choices[0].message = Mock()
            tool_call_response.choices[0].message.content = "I'll calculate that for you"
            
            # Mock tool call
            tool_call = Mock()
            tool_call.function.name = "calculate"
            tool_call.function.arguments = '{"expression": "6*7"}'
            tool_call.id = "call_123"
            tool_call_response.choices[0].message.tool_calls = [tool_call]
            
            # Second response: Agent processes tool result
            final_response = Mock()
            final_response.choices = [Mock()]
            final_response.choices[0].message = Mock()
            final_response.choices[0].message.content = "The answer is 42"
            final_response.choices[0].message.tool_calls = None
            
            # Third response: Agent marks task complete
            completion_response = Mock()
            completion_response.choices = [Mock()]
            completion_response.choices[0].message = Mock()
            completion_response.choices[0].message.content = None
            
            completion_tool_call = Mock()
            completion_tool_call.function.name = "mark_task_complete"
            completion_tool_call.function.arguments = '{"summary": "Calculation completed"}'
            completion_tool_call.id = "call_complete"
            completion_response.choices[0].message.tool_calls = [completion_tool_call]
            
            mock_client.chat.completions.create.side_effect = [
                tool_call_response,
                final_response,
                completion_response
            ]
            
            # Create agent
            agent = OpenRouterAgent(config_path=temp_config_file)
            
            # Mock mark_task_complete tool
            agent.tool_mapping["mark_task_complete"] = lambda **kwargs: {
                "task_complete": True,
                "summary": kwargs.get("summary", "")
            }
            
            # Execute agent
            result = agent.run("Calculate 6 times 7")
            
            # Verify tool was called
            calc_tool.execute.assert_called_with(expression="6*7")
            
            # Verify agent completed successfully
            assert isinstance(result, str)

    @patch('orchestrator.OpenRouterAgent')
    def test_orchestrator_error_handling(self, mock_agent_class, temp_config_file, mock_ui_manager):
        """Test orchestrator error handling with failed agents."""
        # Mock question generation success
        question_agent = Mock()
        question_agent.run.return_value = '["Question 1", "Question 2"]'
        
        # Mock one working agent and one failing agent
        working_agent = Mock()
        working_agent.run.return_value = "Successful response"
        
        failing_agent = Mock()
        failing_agent.run.side_effect = APIError("API failed")
        
        # Mock synthesis agent
        synthesis_agent = Mock()
        synthesis_agent.run.return_value = "Partial synthesis with one failed agent"
        
        mock_agent_class.side_effect = [
            question_agent,
            working_agent,
            failing_agent,
            synthesis_agent
        ]
        
        orchestrator = TaskOrchestrator(
            config_path=temp_config_file,
            ui_manager=mock_ui_manager
        )
        
        # Mock parallel execution with one failure
        with patch('orchestrator.ThreadPoolExecutor') as mock_executor_class:
            mock_executor = Mock()
            mock_executor_class.return_value.__enter__.return_value = mock_executor
            
            # Create futures - one success, one failure
            future1 = Mock()
            future1.result.return_value = {
                "agent_id": 0,
                "status": "completed",
                "response": "Success",
                "execution_time": 1.0
            }
            
            future2 = Mock()
            future2.result.return_value = {
                "agent_id": 1,
                "status": "failed",
                "response": "Agent 1 failed: API failed",
                "execution_time": 0.5
            }
            
            mock_executor.submit.side_effect = [future1, future2]
            
            with patch('orchestrator.as_completed') as mock_as_completed:
                mock_as_completed.return_value = [future1, future2]
                
                # Should handle partial failure gracefully
                result = orchestrator.orchestrate("Test query")
                
                assert result == "Partial synthesis with one failed agent"
                mock_ui_manager.update_orchestrator_phase.assert_called()

    @patch('orchestrator.OpenRouterAgent') 
    def test_orchestrator_timeout_handling(self, mock_agent_class, temp_config_file, mock_ui_manager):
        """Test orchestrator handling of agent timeouts."""
        # Mock question generation
        question_agent = Mock()
        question_agent.run.return_value = '["Question 1", "Question 2"]'
        
        mock_agent_class.side_effect = [question_agent]
        
        orchestrator = TaskOrchestrator(
            config_path=temp_config_file,
            ui_manager=mock_ui_manager
        )
        
        # Mock parallel execution with timeout
        with patch('orchestrator.ThreadPoolExecutor') as mock_executor_class:
            mock_executor = Mock()
            mock_executor_class.return_value.__enter__.return_value = mock_executor
            
            # Mock as_completed to raise TimeoutError
            with patch('orchestrator.as_completed') as mock_as_completed:
                mock_as_completed.side_effect = TimeoutError("Execution timeout")
                
                # Should raise exception on timeout
                with pytest.raises(Exception):
                    orchestrator.orchestrate("Test query")

    def test_ui_manager_integration(self, temp_config_file):
        """Test integration between components and UI manager."""
        ui_manager = UIManager()
        
        # Test agent metrics creation
        metrics = ui_manager.create_agent_metrics("test_agent", 5)
        assert metrics.agent_id == "test_agent"
        assert metrics.max_iterations == 5
        
        # Test status updates
        ui_manager.update_agent_status("test_agent", "running", "Processing")
        assert ui_manager.agent_metrics["test_agent"].status == "running"
        
        # Test timeline logging
        ui_manager.log_timeline("Test event", "Test details")
        assert len(ui_manager.orchestrator_metrics.timeline) == 1
        
        # Test orchestrator phase updates
        ui_manager.update_orchestrator_phase("running_agents", "Executing parallel agents")
        assert ui_manager.orchestrator_metrics.current_phase == "running_agents"

    @patch('agent.discover_tools')
    def test_agent_ui_manager_integration(self, mock_discover_tools, temp_config_file):
        """Test agent integration with UI manager."""
        mock_discover_tools.return_value = {}
        
        ui_manager = UIManager()
        
        with patch('agent.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Mock simple completion response
            response = Mock()
            response.choices = [Mock()]
            response.choices[0].message = Mock()
            response.choices[0].message.content = "Test response"
            response.choices[0].message.tool_calls = None
            mock_client.chat.completions.create.return_value = response
            
            # Create agent with UI manager
            agent = OpenRouterAgent(
                config_path=temp_config_file,
                ui_manager=ui_manager,
                agent_id="test_agent"
            )
            
            # Verify UI manager integration
            assert agent.ui_manager == ui_manager
            assert agent.agent_id == "test_agent"
            assert "test_agent" in ui_manager.agent_metrics

    @patch('orchestrator.OpenRouterAgent')
    def test_question_generation_integration(self, mock_agent_class, temp_config_file, mock_ui_manager):
        """Test question generation integration with orchestrator."""
        # Test various question generation scenarios
        test_scenarios = [
            ('["Q1", "Q2"]', ["Q1", "Q2"]),  # Valid JSON
            ('["Q1", "Q2", "Q3"]', None),    # Wrong number of questions
            ('Invalid JSON', None),           # Invalid JSON format
            ('["Only one question"]', None),  # Too few questions
        ]
        
        for response, expected in test_scenarios:
            question_agent = Mock()
            question_agent.run.return_value = response
            mock_agent_class.return_value = question_agent
            
            orchestrator = TaskOrchestrator(
                config_path=temp_config_file,
                ui_manager=mock_ui_manager
            )
            
            questions = orchestrator.decompose_task("Test input", 2)
            
            if expected:
                assert questions == expected
            else:
                # Should fall back to default questions
                assert len(questions) == 2
                assert "Research comprehensive information about: Test input" in questions[0]


@pytest.mark.integration 
class TestRealComponentIntegration:
    """Integration tests with real components (no mocking)."""

    def test_config_loading_integration(self, test_config):
        """Test that all components can load the same config."""
        import tempfile
        import yaml
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            config_path = f.name
        
        try:
            # Test agent config loading
            with patch('agent.discover_tools') as mock_tools:
                mock_tools.return_value = {}
                agent = OpenRouterAgent(config_path=config_path)
                assert agent.config == test_config
            
            # Test orchestrator config loading  
            orchestrator = TaskOrchestrator(config_path=config_path)
            assert orchestrator.config == test_config
            
            # Test UI manager integration
            ui_manager = UIManager()
            assert ui_manager is not None
            
        finally:
            import os
            os.unlink(config_path)

    def test_tool_discovery_integration(self, test_config):
        """Test tool discovery with real tool classes."""
        from tools import discover_tools
        
        tools = discover_tools(test_config, silent=True)
        
        # Verify all expected tools are discovered
        expected_tools = ["calculate", "read_file", "write_file", "mark_task_complete", "search_web"]
        for tool_name in expected_tools:
            assert tool_name in tools
        
        # Verify tools can generate OpenRouter schemas
        for tool_name, tool_instance in tools.items():
            schema = tool_instance.to_openrouter_schema()
            assert schema["type"] == "function"
            assert "name" in schema["function"]
            assert schema["function"]["name"] == tool_name

    def test_exception_hierarchy_integration(self):
        """Test that custom exceptions work properly across components."""
        from exceptions import (
            MakeItHeavyError, APIError, ToolExecutionError, 
            AgentError, ConfigurationError, OrchestrationError,
            ValidationError, RetryableError
        )
        
        # Test exception hierarchy
        api_error = APIError("API failed", status_code=500)
        assert isinstance(api_error, MakeItHeavyError)
        assert api_error.error_code == "API_ERROR"
        assert api_error.status_code == 500
        
        # Test tool error
        tool_error = ToolExecutionError("test_tool", "Tool failed", {"arg": "value"})
        assert isinstance(tool_error, MakeItHeavyError)
        assert tool_error.tool_name == "test_tool"
        assert tool_error.tool_args == {"arg": "value"}
        
        # Test retryable error
        retry_error = RetryableError("Temporary failure", retry_count=1, max_retries=3)
        assert retry_error.can_retry is True
        
        retry_error_max = RetryableError("Max retries", retry_count=3, max_retries=3)
        assert retry_error_max.can_retry is False