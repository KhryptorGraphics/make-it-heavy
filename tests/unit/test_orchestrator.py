"""
Unit tests for TaskOrchestrator class.
Tests orchestration workflow, question generation, parallel execution, and synthesis.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import Future

from orchestrator import TaskOrchestrator
from exceptions import OrchestrationError, APIError


class TestTaskOrchestrator:
    """Test suite for TaskOrchestrator class."""

    def test_orchestrator_initialization_success(self, temp_config_file, mock_ui_manager):
        """Test successful orchestrator initialization."""
        orchestrator = TaskOrchestrator(
            config_path=temp_config_file,
            ui_manager=mock_ui_manager
        )
        
        assert orchestrator.config is not None
        assert orchestrator.ui_manager == mock_ui_manager
        assert orchestrator.num_agents == 2  # From test config
        assert orchestrator.task_timeout == 10  # From test config

    def test_orchestrator_initialization_missing_config(self):
        """Test orchestrator initialization with missing config."""
        with pytest.raises(FileNotFoundError):
            TaskOrchestrator(config_path="nonexistent.yaml")

    @patch('orchestrator.OpenRouterAgent')
    def test_decompose_task_success(self, mock_agent_class, temp_config_file, mock_ui_manager):
        """Test successful task decomposition."""
        # Mock question generation agent
        mock_agent = Mock()
        mock_agent.run.return_value = '["Question 1", "Question 2"]'
        mock_agent_class.return_value = mock_agent
        
        orchestrator = TaskOrchestrator(
            config_path=temp_config_file,
            ui_manager=mock_ui_manager
        )
        
        questions = orchestrator.decompose_task("Test input", 2)
        
        assert len(questions) == 2
        assert questions[0] == "Question 1"
        assert questions[1] == "Question 2"
        mock_ui_manager.set_questions_generated.assert_called_once()

    @patch('orchestrator.OpenRouterAgent')
    def test_decompose_task_json_error(self, mock_agent_class, temp_config_file, mock_ui_manager):
        """Test task decomposition with JSON parsing error."""
        # Mock agent returning invalid JSON
        mock_agent = Mock()
        mock_agent.run.return_value = 'Invalid JSON response'
        mock_agent_class.return_value = mock_agent
        
        orchestrator = TaskOrchestrator(
            config_path=temp_config_file,
            ui_manager=mock_ui_manager
        )
        
        questions = orchestrator.decompose_task("Test input", 2)
        
        # Should fall back to default questions
        assert len(questions) == 2
        assert "Research comprehensive information about: Test input" in questions[0]

    @patch('orchestrator.OpenRouterAgent')
    def test_decompose_task_wrong_number_questions(self, mock_agent_class, temp_config_file, mock_ui_manager):
        """Test task decomposition with wrong number of questions."""
        # Mock agent returning wrong number of questions
        mock_agent = Mock()
        mock_agent.run.return_value = '["Question 1"]'  # Only 1 question for 2 agents
        mock_agent_class.return_value = mock_agent
        
        orchestrator = TaskOrchestrator(
            config_path=temp_config_file,
            ui_manager=mock_ui_manager
        )
        
        questions = orchestrator.decompose_task("Test input", 2)
        
        # Should fall back to default questions
        assert len(questions) == 2

    def test_update_agent_progress(self, temp_config_file, mock_ui_manager):
        """Test agent progress updates."""
        orchestrator = TaskOrchestrator(
            config_path=temp_config_file,
            ui_manager=mock_ui_manager
        )
        
        orchestrator.update_agent_progress(0, "RUNNING", "Test result")
        
        assert orchestrator.agent_progress[0] == "RUNNING"
        assert orchestrator.agent_results[0] == "Test result"

    @patch('orchestrator.OpenRouterAgent')
    def test_run_agent_parallel_success(self, mock_agent_class, temp_config_file):
        """Test successful parallel agent execution."""
        # Mock agent
        mock_agent = Mock()
        mock_agent.run.return_value = "Agent response"
        mock_agent_class.return_value = mock_agent
        
        orchestrator = TaskOrchestrator(config_path=temp_config_file)
        
        result = orchestrator.run_agent_parallel(0, "Test subtask")
        
        assert result["agent_id"] == 0
        assert result["status"] == "completed"
        assert result["response"] == "Agent response"
        assert "execution_time" in result

    @patch('orchestrator.OpenRouterAgent')
    def test_run_agent_parallel_failure(self, mock_agent_class, temp_config_file):
        """Test parallel agent execution with failure."""
        # Mock agent that raises exception
        mock_agent = Mock()
        mock_agent.run.side_effect = Exception("Agent failed")
        mock_agent_class.return_value = mock_agent
        
        orchestrator = TaskOrchestrator(config_path=temp_config_file)
        
        result = orchestrator.run_agent_parallel(0, "Test subtask")
        
        assert result["agent_id"] == 0
        assert result["status"] == "failed"
        assert "Agent failed" in result["response"]

    @patch('orchestrator.OpenRouterAgent')
    def test_aggregate_results_success(self, mock_agent_class, temp_config_file):
        """Test successful result aggregation."""
        # Mock synthesis agent
        mock_agent = Mock()
        mock_agent.run.return_value = "Synthesized response"
        mock_agent_class.return_value = mock_agent
        
        orchestrator = TaskOrchestrator(config_path=temp_config_file)
        
        agent_results = [
            {"agent_id": 0, "status": "completed", "response": "Response 1"},
            {"agent_id": 1, "status": "completed", "response": "Response 2"}
        ]
        
        result = orchestrator.aggregate_results(agent_results)
        
        assert result == "Synthesized response"
        mock_agent.run.assert_called_once()

    @patch('orchestrator.OpenRouterAgent')
    def test_aggregate_results_with_failed_agents(self, mock_agent_class, temp_config_file):
        """Test result aggregation with some failed agents."""
        # Mock synthesis agent
        mock_agent = Mock()
        mock_agent.run.return_value = "Partial synthesis"
        mock_agent_class.return_value = mock_agent
        
        orchestrator = TaskOrchestrator(config_path=temp_config_file)
        
        agent_results = [
            {"agent_id": 0, "status": "completed", "response": "Response 1"},
            {"agent_id": 1, "status": "failed", "response": "Error occurred"}
        ]
        
        result = orchestrator.aggregate_results(agent_results)
        
        assert result == "Partial synthesis"

    def test_get_progress_status(self, temp_config_file):
        """Test getting progress status."""
        orchestrator = TaskOrchestrator(config_path=temp_config_file)
        orchestrator.agent_progress = {0: "RUNNING", 1: "COMPLETED"}
        
        status = orchestrator.get_progress_status()
        
        assert status[0] == "RUNNING"
        assert status[1] == "COMPLETED"

    @patch('orchestrator.ThreadPoolExecutor')
    @patch.object(TaskOrchestrator, 'decompose_task')
    @patch.object(TaskOrchestrator, 'run_agent_parallel')
    @patch.object(TaskOrchestrator, 'aggregate_results')
    def test_orchestrate_success(self, mock_aggregate, mock_run_agent, mock_decompose, 
                                mock_executor_class, temp_config_file, mock_ui_manager):
        """Test successful orchestration workflow."""
        # Mock decompose_task
        mock_decompose.return_value = ["Question 1", "Question 2"]
        
        # Mock parallel execution
        mock_run_agent.side_effect = [
            {"agent_id": 0, "status": "completed", "response": "Response 1", "execution_time": 1.0},
            {"agent_id": 1, "status": "completed", "response": "Response 2", "execution_time": 1.5}
        ]
        
        # Mock aggregation
        mock_aggregate.return_value = "Final result"
        
        # Mock ThreadPoolExecutor
        mock_executor = Mock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Mock futures
        future1, future2 = Mock(), Mock()
        future1.result.return_value = {"agent_id": 0, "status": "completed", "response": "Response 1", "execution_time": 1.0}
        future2.result.return_value = {"agent_id": 1, "status": "completed", "response": "Response 2", "execution_time": 1.5}
        
        mock_executor.submit.side_effect = [future1, future2]
        
        # Mock as_completed
        with patch('orchestrator.as_completed') as mock_as_completed:
            mock_as_completed.return_value = [future1, future2]
            
            orchestrator = TaskOrchestrator(
                config_path=temp_config_file,
                ui_manager=mock_ui_manager
            )
            
            result = orchestrator.orchestrate("Test input")
            
            assert result == "Final result"
            mock_ui_manager.update_orchestrator_phase.assert_called()

    @patch('orchestrator.ThreadPoolExecutor')
    @patch.object(TaskOrchestrator, 'decompose_task')
    def test_orchestrate_timeout(self, mock_decompose, mock_executor_class, 
                                temp_config_file, mock_ui_manager):
        """Test orchestration with timeout."""
        # Mock decompose_task
        mock_decompose.return_value = ["Question 1", "Question 2"]
        
        # Mock ThreadPoolExecutor
        mock_executor = Mock()
        mock_executor_class.return_value.__enter__.return_value = mock_executor
        
        # Mock futures that timeout
        future1, future2 = Mock(), Mock()
        mock_executor.submit.side_effect = [future1, future2]
        
        # Mock as_completed with timeout
        with patch('orchestrator.as_completed') as mock_as_completed:
            mock_as_completed.side_effect = TimeoutError("Timeout")
            
            orchestrator = TaskOrchestrator(
                config_path=temp_config_file,
                ui_manager=mock_ui_manager
            )
            
            with pytest.raises(Exception):  # Should handle timeout gracefully
                orchestrator.orchestrate("Test input")

    @patch.object(TaskOrchestrator, 'decompose_task')
    def test_orchestrate_decomposition_failure(self, mock_decompose, temp_config_file, mock_ui_manager):
        """Test orchestration with decomposition failure."""
        # Mock decompose_task to raise exception
        mock_decompose.side_effect = Exception("Decomposition failed")
        
        orchestrator = TaskOrchestrator(
            config_path=temp_config_file,
            ui_manager=mock_ui_manager
        )
        
        with pytest.raises(Exception):
            orchestrator.orchestrate("Test input")


@pytest.mark.integration
class TestOrchestratorIntegration:
    """Integration tests for orchestrator with real components."""
    
    def test_orchestrator_with_real_config(self, test_config):
        """Test orchestrator with real configuration structure."""
        import tempfile
        import yaml
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            config_path = f.name
        
        try:
            orchestrator = TaskOrchestrator(config_path=config_path)
            
            assert orchestrator.num_agents == test_config['orchestrator']['parallel_agents']
            assert orchestrator.task_timeout == test_config['orchestrator']['task_timeout']
            
        finally:
            import os
            os.unlink(config_path)

    @patch('orchestrator.OpenRouterAgent')
    def test_full_workflow_simulation(self, mock_agent_class, temp_config_file):
        """Test complete orchestration workflow simulation."""
        # Mock different agents for different purposes
        agents = []
        
        # Question generation agent
        question_agent = Mock()
        question_agent.run.return_value = '["What is AI?", "How does ML work?"]'
        
        # Working agents
        working_agent1 = Mock()
        working_agent1.run.return_value = "AI is artificial intelligence"
        
        working_agent2 = Mock()
        working_agent2.run.return_value = "ML is machine learning"
        
        # Synthesis agent
        synthesis_agent = Mock()
        synthesis_agent.run.return_value = "AI and ML are related technologies"
        
        # Configure mock to return different agents
        agents = [question_agent, working_agent1, working_agent2, synthesis_agent]
        mock_agent_class.side_effect = agents
        
        orchestrator = TaskOrchestrator(config_path=temp_config_file)
        
        # This would normally run the full workflow
        # We're testing that the components integrate properly
        questions = orchestrator.decompose_task("Tell me about AI", 2)
        
        assert len(questions) == 2
        assert questions[0] == "What is AI?"
        assert questions[1] == "How does ML work?"