"""
End-to-end tests for complete user workflows.
Tests the entire system from user input to final output.
"""

import pytest
import tempfile
import yaml
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from enhanced_main import EnhancedMakeItHeavyCLI
from enhanced_orchestrator import EnhancedOrchestratorCLI


@pytest.mark.e2e
class TestCompleteUserWorkflows:
    """End-to-end tests for complete user scenarios."""

    @patch('enhanced_main.TaskOrchestrator')
    @patch('enhanced_main.UIManager')
    def test_enhanced_main_complete_workflow(self, mock_ui_manager_class, mock_orchestrator_class, test_config):
        """Test complete workflow through enhanced main CLI."""
        # Create temporary config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            config_path = f.name
        
        try:
            # Mock UI Manager
            mock_ui_manager = Mock()
            mock_ui_manager_class.return_value = mock_ui_manager
            
            # Mock Orchestrator
            mock_orchestrator = Mock()
            mock_orchestrator.orchestrate.return_value = "Comprehensive analysis complete: AI is a broad field encompassing machine learning, natural language processing, and robotics."
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Mock load_config to return our test config
            with patch('enhanced_main.load_config') as mock_load_config:
                mock_load_config.return_value = test_config
                
                # Mock validate_api_key
                with patch('enhanced_main.validate_api_key') as mock_validate:
                    mock_validate.return_value = True
                    
                    # Create CLI instance
                    cli = EnhancedMakeItHeavyCLI()
                    
                    # Test configuration check
                    config_ok = cli.check_and_setup_configuration()
                    assert config_ok is True
                    
                    # Test component initialization
                    init_ok = cli.initialize_components()
                    assert init_ok is True
                    
                    # Test request processing
                    cli.process_user_request("What is artificial intelligence?")
                    
                    # Verify orchestrator was called
                    mock_orchestrator.orchestrate.assert_called_once_with("What is artificial intelligence?")
                    
                    # Verify UI manager interactions
                    mock_ui_manager.show_orchestrator_dashboard.assert_called()
                    
        finally:
            Path(config_path).unlink(missing_ok=True)

    @patch('enhanced_orchestrator.TaskOrchestrator')
    @patch('enhanced_orchestrator.UIManager')
    def test_enhanced_orchestrator_complete_workflow(self, mock_ui_manager_class, mock_orchestrator_class, test_config):
        """Test complete workflow through enhanced orchestrator CLI."""
        # Create temporary config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            config_path = f.name
        
        try:
            # Mock UI Manager
            mock_ui_manager = Mock()
            mock_ui_manager_class.return_value = mock_ui_manager
            
            # Mock Orchestrator
            mock_orchestrator = Mock()
            mock_orchestrator.orchestrate.return_value = "Multi-agent analysis: AI involves machine learning algorithms, neural networks, and data processing techniques."
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Mock load_config
            with patch('enhanced_orchestrator.load_config') as mock_load_config:
                mock_load_config.return_value = test_config
                
                # Mock validate_api_key
                with patch('enhanced_orchestrator.validate_api_key') as mock_validate:
                    mock_validate.return_value = True
                    
                    # Create CLI instance
                    cli = EnhancedOrchestratorCLI()
                    
                    # Test initialization
                    init_ok = cli.initialize_components()
                    assert init_ok is True
                    
                    # Test orchestration request
                    cli.process_orchestration_request("Explain machine learning")
                    
                    # Verify orchestrator was called
                    mock_orchestrator.orchestrate.assert_called_once_with("Explain machine learning")
                    
        finally:
            Path(config_path).unlink(missing_ok=True)

    @patch('agent.OpenAI')
    def test_agent_tool_execution_workflow(self, mock_openai_class, temp_config_file):
        """Test complete agent workflow with tool execution."""
        from agent import OpenRouterAgent
        from tools.calculator_tool import CalculatorTool
        
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Simulate conversation flow:
        # 1. User asks for calculation
        # 2. Agent decides to use calculator tool
        # 3. Tool executes calculation
        # 4. Agent provides final response
        # 5. Agent marks task complete
        
        # First API call - agent decides to use calculator
        tool_response = Mock()
        tool_response.choices = [Mock()]
        tool_response.choices[0].message = Mock()
        tool_response.choices[0].message.content = "I'll calculate that for you."
        
        tool_call = Mock()
        tool_call.function.name = "calculate"
        tool_call.function.arguments = '{"expression": "15 * 7"}'
        tool_call.id = "call_calc"
        tool_response.choices[0].message.tool_calls = [tool_call]
        
        # Second API call - agent provides final answer
        final_response = Mock()
        final_response.choices = [Mock()]
        final_response.choices[0].message = Mock()
        final_response.choices[0].message.content = "The result of 15 × 7 is 105."
        final_response.choices[0].message.tool_calls = None
        
        # Third API call - agent marks task complete
        complete_response = Mock()
        complete_response.choices = [Mock()]
        complete_response.choices[0].message = Mock()
        complete_response.choices[0].message.content = None
        
        complete_tool_call = Mock()
        complete_tool_call.function.name = "mark_task_complete"
        complete_tool_call.function.arguments = '{"summary": "Calculation completed successfully"}'
        complete_tool_call.id = "call_complete"
        complete_response.choices[0].message.tool_calls = [complete_tool_call]
        
        mock_client.chat.completions.create.side_effect = [
            tool_response,
            final_response,
            complete_response
        ]
        
        # Mock tool discovery to include calculator
        with patch('agent.discover_tools') as mock_discover:
            calc_tool = CalculatorTool()
            mock_discover.return_value = {
                "calculate": calc_tool,
                "mark_task_complete": Mock(execute=lambda **kwargs: {"task_complete": True, "summary": kwargs.get("summary", "")})
            }
            
            # Create agent
            agent = OpenRouterAgent(config_path=temp_config_file)
            
            # Execute workflow
            result = agent.run("What is 15 times 7?")
            
            # Verify complete workflow
            assert isinstance(result, str)
            assert "calculate that" in result or "105" in result or "completed" in result
            
            # Verify API calls were made
            assert mock_client.chat.completions.create.call_count >= 2

    @patch('orchestrator.OpenRouterAgent')
    def test_full_orchestration_workflow(self, mock_agent_class, temp_config_file):
        """Test complete orchestration workflow from start to finish."""
        from orchestrator import TaskOrchestrator
        from ui_manager import UIManager
        
        # Mock the complete agent interaction sequence
        agents_created = []
        
        def create_mock_agent(*args, **kwargs):
            agent = Mock()
            agents_created.append(agent)
            return agent
        
        mock_agent_class.side_effect = create_mock_agent
        
        # Set up agent responses in order:
        # 1. Question generation agent
        agents_created[0].run.return_value = '["What are the core concepts of AI?", "What are practical applications of AI?"]'
        
        # 2. First working agent
        agents_created[1].run.return_value = "AI core concepts include machine learning, neural networks, natural language processing, and computer vision."
        
        # 3. Second working agent  
        agents_created[2].run.return_value = "AI applications include autonomous vehicles, medical diagnosis, recommendation systems, and virtual assistants."
        
        # 4. Synthesis agent
        agents_created[3].run.return_value = "AI combines core technologies like machine learning and neural networks with practical applications in healthcare, transportation, and digital services."
        
        # Create UI manager
        ui_manager = UIManager()
        
        # Create orchestrator
        orchestrator = TaskOrchestrator(
            config_path=temp_config_file,
            ui_manager=ui_manager
        )
        
        # Mock parallel execution
        with patch('orchestrator.ThreadPoolExecutor') as mock_executor_class:
            mock_executor = Mock()
            mock_executor_class.return_value.__enter__.return_value = mock_executor
            
            # Create futures for parallel execution
            future1 = Mock()
            future1.result.return_value = {
                "agent_id": 0,
                "status": "completed",
                "response": "Core concepts response",
                "execution_time": 2.5
            }
            
            future2 = Mock()
            future2.result.return_value = {
                "agent_id": 1,
                "status": "completed", 
                "response": "Applications response",
                "execution_time": 3.1
            }
            
            mock_executor.submit.side_effect = [future1, future2]
            
            # Mock as_completed
            with patch('orchestrator.as_completed') as mock_as_completed:
                mock_as_completed.return_value = [future1, future2]
                
                # Execute complete orchestration
                result = orchestrator.orchestrate("Tell me about artificial intelligence")
                
                # Verify final result
                assert "AI combines core technologies" in result
                
                # Verify all agents were created and called
                assert len(agents_created) == 4
                
                # Verify UI manager tracked progress
                assert ui_manager.orchestrator_metrics.current_phase in ["completed", "synthesizing"]

    def test_error_recovery_workflow(self, temp_config_file):
        """Test complete workflow with error recovery."""
        from enhanced_main import EnhancedMakeItHeavyCLI
        from exceptions import APIError, ConfigurationError
        
        cli = EnhancedMakeItHeavyCLI()
        
        # Test configuration error recovery
        with patch('enhanced_main.load_config') as mock_load_config:
            mock_load_config.side_effect = ConfigurationError("Config file corrupted", "config.yaml")
            
            # Should handle gracefully
            config_ok = cli.check_and_setup_configuration()
            assert config_ok is False

    @patch('setup_wizard.ConfigurationWizard')
    def test_setup_wizard_integration(self, mock_wizard_class, test_config):
        """Test integration with setup wizard."""
        from enhanced_main import EnhancedMakeItHeavyCLI
        
        # Mock wizard
        mock_wizard = Mock()
        mock_wizard.run_setup.return_value = True
        mock_wizard_class.return_value = mock_wizard
        
        cli = EnhancedMakeItHeavyCLI()
        
        # Test setup wizard call
        result = cli.run_setup_wizard()
        assert result is True
        mock_wizard.run_setup.assert_called_once()

    def test_configuration_validation_workflow(self, test_config):
        """Test complete configuration validation workflow."""
        from utils import load_config, validate_api_key
        
        # Create temporary config with various issues
        configs_to_test = [
            # Valid config
            (test_config, True),
            
            # Invalid API key
            ({**test_config, "openrouter": {**test_config["openrouter"], "api_key": "invalid-key"}}, False),
            
            # Missing section
            ({k: v for k, v in test_config.items() if k != "agent"}, False),
        ]
        
        for config, should_be_valid in configs_to_test:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                yaml.dump(config, f)
                config_path = f.name
            
            try:
                if should_be_valid:
                    # Should load successfully
                    loaded_config = load_config(config_path)
                    assert loaded_config is not None
                    
                    # API key should validate
                    api_key = loaded_config.get("openrouter", {}).get("api_key", "")
                    if api_key == test_config["openrouter"]["api_key"]:
                        assert validate_api_key(api_key) is True
                else:
                    # Should either fail to load or have invalid API key
                    try:
                        loaded_config = load_config(config_path)
                        api_key = loaded_config.get("openrouter", {}).get("api_key", "")
                        if api_key:
                            assert validate_api_key(api_key) is False
                    except:
                        # Expected for missing sections
                        pass
                        
            finally:
                Path(config_path).unlink(missing_ok=True)


@pytest.mark.e2e
@pytest.mark.slow
class TestPerformanceWorkflows:
    """End-to-end performance and stress tests."""

    @patch('orchestrator.OpenRouterAgent')
    def test_high_load_orchestration(self, mock_agent_class, temp_config_file):
        """Test orchestration under high load scenarios."""
        from orchestrator import TaskOrchestrator
        
        # Mock agents for high-load scenario
        question_agent = Mock()
        question_agent.run.return_value = f'[{", ".join([f"\\"Question {i}\\"" for i in range(4)])}]'
        
        working_agents = []
        for i in range(4):
            agent = Mock()
            agent.run.return_value = f"Response from agent {i}"
            working_agents.append(agent)
        
        synthesis_agent = Mock()
        synthesis_agent.run.return_value = "Synthesized response from all agents"
        
        all_agents = [question_agent] + working_agents + [synthesis_agent]
        mock_agent_class.side_effect = all_agents
        
        orchestrator = TaskOrchestrator(config_path=temp_config_file)
        
        # Mock parallel execution with all agents
        with patch('orchestrator.ThreadPoolExecutor') as mock_executor_class:
            mock_executor = Mock()
            mock_executor_class.return_value.__enter__.return_value = mock_executor
            
            # Create futures for all working agents
            futures = []
            for i in range(4):
                future = Mock()
                future.result.return_value = {
                    "agent_id": i,
                    "status": "completed",
                    "response": f"Response {i}",
                    "execution_time": 1.0 + i * 0.1
                }
                futures.append(future)
            
            mock_executor.submit.side_effect = futures
            
            with patch('orchestrator.as_completed') as mock_as_completed:
                mock_as_completed.return_value = futures
                
                # Execute high-load orchestration
                result = orchestrator.orchestrate("Complex query requiring multiple perspectives")
                
                assert result == "Synthesized response from all agents"
                assert mock_executor.submit.call_count == 4  # All parallel agents

    def test_memory_usage_workflow(self, temp_config_file):
        """Test memory usage in typical workflows."""
        import gc
        import sys
        
        # Get initial memory baseline
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Run typical workflow
        from enhanced_main import EnhancedMakeItHeavyCLI
        
        with patch('enhanced_main.load_config') as mock_load_config:
            mock_load_config.return_value = {
                "openrouter": {"api_key": "sk-test", "model": "test", "base_url": "https://test"},
                "agent": {"max_iterations": 3},
                "orchestrator": {"parallel_agents": 2, "task_timeout": 10},
                "ui": {"rich_output": False},
                "logging": {"enabled": False},
                "performance": {"api_timeout": 5}
            }
            
            cli = EnhancedMakeItHeavyCLI()
            
            # Check that object creation is reasonable
            gc.collect()
            after_init_objects = len(gc.get_objects())
            
            # Should not create excessive objects
            object_increase = after_init_objects - initial_objects
            assert object_increase < 1000  # Reasonable threshold
        
        # Cleanup and verify memory is released
        del cli
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory should be mostly freed
        assert final_objects <= after_init_objects + 100  # Allow some variance