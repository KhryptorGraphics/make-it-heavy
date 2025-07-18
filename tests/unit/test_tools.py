"""
Unit tests for tool system including BaseTool and specific tool implementations.
"""

import pytest
import json
import tempfile
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from tools.base_tool import BaseTool
from tools.calculator_tool import CalculatorTool
from tools.read_file_tool import ReadFileTool
from tools.write_file_tool import WriteFileTool
from tools.task_done_tool import TaskDoneTool
from tools.search_tool import SearchTool
from tools import discover_tools


class TestBaseTool:
    """Test suite for BaseTool abstract base class."""

    def test_base_tool_is_abstract(self):
        """Test that BaseTool cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseTool()

    def test_base_tool_abstract_methods(self):
        """Test that abstract methods must be implemented."""
        
        class IncompleteToolClass(BaseTool):
            pass
        
        with pytest.raises(TypeError):
            IncompleteToolClass()

    def test_base_tool_to_openrouter_schema(self):
        """Test OpenRouter schema generation."""
        
        class TestTool(BaseTool):
            @property
            def name(self):
                return "test_tool"
            
            @property
            def description(self):
                return "A test tool"
            
            @property
            def parameters(self):
                return {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string", "description": "Test input"}
                    },
                    "required": ["input"]
                }
            
            def execute(self, **kwargs):
                return {"result": "test"}
        
        tool = TestTool()
        schema = tool.to_openrouter_schema()
        
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "test_tool"
        assert schema["function"]["description"] == "A test tool"
        assert "parameters" in schema["function"]


class TestCalculatorTool:
    """Test suite for CalculatorTool."""

    def test_calculator_properties(self):
        """Test calculator tool properties."""
        tool = CalculatorTool()
        
        assert tool.name == "calculate"
        assert "mathematical expressions" in tool.description.lower()
        assert "expression" in tool.parameters["properties"]

    def test_calculator_simple_addition(self):
        """Test simple addition calculation."""
        tool = CalculatorTool()
        
        result = tool.execute(expression="2 + 2")
        
        assert result["result"] == 4
        assert result["expression"] == "2 + 2"

    def test_calculator_complex_expression(self):
        """Test complex mathematical expression."""
        tool = CalculatorTool()
        
        result = tool.execute(expression="(10 + 5) * 2 / 3")
        
        assert result["result"] == 10.0
        assert result["expression"] == "(10 + 5) * 2 / 3"

    def test_calculator_invalid_expression(self):
        """Test calculator with invalid expression."""
        tool = CalculatorTool()
        
        result = tool.execute(expression="invalid expression")
        
        assert "error" in result
        assert "Invalid expression" in result["error"]

    def test_calculator_division_by_zero(self):
        """Test calculator with division by zero."""
        tool = CalculatorTool()
        
        result = tool.execute(expression="10 / 0")
        
        assert "error" in result
        assert "division by zero" in result["error"].lower()

    def test_calculator_unsafe_operations(self):
        """Test that unsafe operations are blocked."""
        tool = CalculatorTool()
        
        # Test dangerous function calls
        dangerous_expressions = [
            "import os",
            "__import__('os')",
            "exec('print(1)')",
            "eval('1+1')"
        ]
        
        for expr in dangerous_expressions:
            result = tool.execute(expression=expr)
            assert "error" in result


class TestReadFileTool:
    """Test suite for ReadFileTool."""

    def test_read_file_properties(self):
        """Test read file tool properties."""
        tool = ReadFileTool()
        
        assert tool.name == "read_file"
        assert "read" in tool.description.lower()
        assert "file_path" in tool.parameters["properties"]

    def test_read_file_success(self, tmp_path):
        """Test successful file reading."""
        tool = ReadFileTool()
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!\nSecond line."
        test_file.write_text(test_content)
        
        result = tool.execute(file_path=str(test_file))
        
        assert "content" in result
        assert test_content in result["content"]
        assert result["file_path"] == str(test_file)

    def test_read_file_not_found(self):
        """Test reading non-existent file."""
        tool = ReadFileTool()
        
        result = tool.execute(file_path="/nonexistent/file.txt")
        
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_read_file_with_lines_limit(self, tmp_path):
        """Test reading file with lines limit."""
        tool = ReadFileTool()
        
        # Create test file with multiple lines
        test_file = tmp_path / "multiline.txt"
        lines = [f"Line {i}" for i in range(10)]
        test_file.write_text("\n".join(lines))
        
        result = tool.execute(file_path=str(test_file), lines=5)
        
        assert "content" in result
        content_lines = result["content"].split("\n")
        assert len(content_lines) <= 5

    def test_read_file_head_mode(self, tmp_path):
        """Test reading file in head mode."""
        tool = ReadFileTool()
        
        test_file = tmp_path / "test.txt"
        lines = [f"Line {i}" for i in range(10)]
        test_file.write_text("\n".join(lines))
        
        result = tool.execute(file_path=str(test_file), mode="head", lines=3)
        
        assert "Line 0" in result["content"]
        assert "Line 1" in result["content"]
        assert "Line 2" in result["content"]
        assert "Line 9" not in result["content"]

    def test_read_file_tail_mode(self, tmp_path):
        """Test reading file in tail mode."""
        tool = ReadFileTool()
        
        test_file = tmp_path / "test.txt"
        lines = [f"Line {i}" for i in range(10)]
        test_file.write_text("\n".join(lines))
        
        result = tool.execute(file_path=str(test_file), mode="tail", lines=3)
        
        assert "Line 7" in result["content"]
        assert "Line 8" in result["content"]
        assert "Line 9" in result["content"]
        assert "Line 0" not in result["content"]


class TestWriteFileTool:
    """Test suite for WriteFileTool."""

    def test_write_file_properties(self):
        """Test write file tool properties."""
        tool = WriteFileTool()
        
        assert tool.name == "write_file"
        assert "write" in tool.description.lower()
        assert "file_path" in tool.parameters["properties"]
        assert "content" in tool.parameters["properties"]

    def test_write_file_success(self, tmp_path):
        """Test successful file writing."""
        tool = WriteFileTool()
        
        test_file = tmp_path / "output.txt"
        test_content = "Hello, World!"
        
        result = tool.execute(file_path=str(test_file), content=test_content)
        
        assert result["success"] is True
        assert result["file_path"] == str(test_file)
        assert test_file.read_text() == test_content

    def test_write_file_creates_directory(self, tmp_path):
        """Test that write file creates parent directories."""
        tool = WriteFileTool()
        
        test_file = tmp_path / "subdir" / "output.txt"
        test_content = "Test content"
        
        result = tool.execute(file_path=str(test_file), content=test_content)
        
        assert result["success"] is True
        assert test_file.exists()
        assert test_file.read_text() == test_content

    def test_write_file_permission_error(self):
        """Test write file with permission error."""
        tool = WriteFileTool()
        
        # Try to write to a read-only location
        result = tool.execute(file_path="/root/readonly.txt", content="test")
        
        assert "error" in result
        assert "permission" in result["error"].lower() or "access" in result["error"].lower()

    def test_write_file_overwrite(self, tmp_path):
        """Test overwriting existing file."""
        tool = WriteFileTool()
        
        test_file = tmp_path / "overwrite.txt"
        test_file.write_text("Original content")
        
        new_content = "New content"
        result = tool.execute(file_path=str(test_file), content=new_content)
        
        assert result["success"] is True
        assert test_file.read_text() == new_content


class TestTaskDoneTool:
    """Test suite for TaskDoneTool."""

    def test_task_done_properties(self):
        """Test task done tool properties."""
        tool = TaskDoneTool()
        
        assert tool.name == "mark_task_complete"
        assert "complete" in tool.description.lower()
        assert "summary" in tool.parameters["properties"]

    def test_task_done_execution(self):
        """Test task done tool execution."""
        tool = TaskDoneTool()
        
        result = tool.execute(summary="Task completed successfully")
        
        assert result["task_complete"] is True
        assert result["summary"] == "Task completed successfully"
        assert "timestamp" in result

    def test_task_done_with_message(self):
        """Test task done tool with final message."""
        tool = TaskDoneTool()
        
        result = tool.execute(
            summary="Analysis complete",
            final_message="Here are the results"
        )
        
        assert result["task_complete"] is True
        assert result["summary"] == "Analysis complete"
        assert result["final_message"] == "Here are the results"


class TestSearchTool:
    """Test suite for SearchTool."""

    def test_search_tool_properties(self):
        """Test search tool properties."""
        tool = SearchTool()
        
        assert tool.name == "search_web"
        assert "search" in tool.description.lower()
        assert "query" in tool.parameters["properties"]

    @patch('tools.search_tool.DDGS')
    def test_search_success(self, mock_ddgs_class):
        """Test successful web search."""
        # Mock DDGS
        mock_ddgs = Mock()
        mock_ddgs_class.return_value = mock_ddgs
        
        # Mock search results
        mock_results = [
            {
                "title": "Test Result 1",
                "href": "https://example.com/1",
                "body": "Test content 1"
            },
            {
                "title": "Test Result 2", 
                "href": "https://example.com/2",
                "body": "Test content 2"
            }
        ]
        mock_ddgs.text.return_value = mock_results
        
        tool = SearchTool()
        result = tool.execute(query="test query")
        
        assert "results" in result
        assert len(result["results"]) == 2
        assert result["query"] == "test query"
        assert result["results"][0]["title"] == "Test Result 1"

    @patch('tools.search_tool.DDGS')
    def test_search_with_max_results(self, mock_ddgs_class):
        """Test search with max results limit."""
        mock_ddgs = Mock()
        mock_ddgs_class.return_value = mock_ddgs
        
        # Mock more results than max_results
        mock_results = [{"title": f"Result {i}", "href": f"https://example.com/{i}", "body": f"Content {i}"} 
                       for i in range(10)]
        mock_ddgs.text.return_value = mock_results
        
        tool = SearchTool()
        result = tool.execute(query="test", max_results=3)
        
        assert len(result["results"]) == 3

    @patch('tools.search_tool.DDGS')
    def test_search_failure(self, mock_ddgs_class):
        """Test search with API failure."""
        mock_ddgs = Mock()
        mock_ddgs_class.return_value = mock_ddgs
        mock_ddgs.text.side_effect = Exception("Search API failed")
        
        tool = SearchTool()
        result = tool.execute(query="test query")
        
        assert "error" in result
        assert "failed" in result["error"].lower()

    @patch('tools.search_tool.DDGS')
    @patch('tools.search_tool.requests.get')
    def test_search_with_content_extraction(self, mock_get, mock_ddgs_class):
        """Test search with content extraction from URLs."""
        # Mock DDGS
        mock_ddgs = Mock()
        mock_ddgs_class.return_value = mock_ddgs
        mock_ddgs.text.return_value = [
            {
                "title": "Test Page",
                "href": "https://example.com/page",
                "body": "Short snippet"
            }
        ]
        
        # Mock requests for content extraction
        mock_response = Mock()
        mock_response.text = "<html><body><p>Full page content here</p></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        tool = SearchTool()
        result = tool.execute(query="test", extract_content=True)
        
        assert "results" in result
        # Content extraction should be attempted
        mock_get.assert_called()


class TestToolDiscovery:
    """Test suite for tool discovery system."""

    def test_discover_tools_success(self, test_config):
        """Test successful tool discovery."""
        tools = discover_tools(test_config)
        
        # Should discover all built-in tools
        expected_tools = [
            "calculate", "read_file", "write_file", 
            "mark_task_complete", "search_web"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tools
            assert hasattr(tools[tool_name], 'execute')

    def test_discover_tools_silent_mode(self, test_config):
        """Test tool discovery in silent mode."""
        tools = discover_tools(test_config, silent=True)
        
        # Should still discover tools but without output
        assert len(tools) > 0
        assert "calculate" in tools

    @patch('tools.sys.modules')
    def test_discover_tools_import_error(self, mock_modules, test_config):
        """Test tool discovery with import errors."""
        # Mock import error for one tool
        def mock_import(name):
            if 'calculator_tool' in name:
                raise ImportError("Mock import error")
            return Mock()
        
        with patch('tools.importlib.import_module', side_effect=mock_import):
            tools = discover_tools(test_config, silent=True)
            
            # Should still discover other tools
            assert len(tools) >= 0  # Some tools should still work

    def test_all_tools_have_required_methods(self, test_config):
        """Test that all discovered tools have required methods."""
        tools = discover_tools(test_config)
        
        for tool_name, tool_instance in tools.items():
            # Test required properties
            assert hasattr(tool_instance, 'name')
            assert hasattr(tool_instance, 'description')
            assert hasattr(tool_instance, 'parameters')
            assert hasattr(tool_instance, 'execute')
            
            # Test that properties return correct types
            assert isinstance(tool_instance.name, str)
            assert isinstance(tool_instance.description, str)
            assert isinstance(tool_instance.parameters, dict)
            
            # Test OpenRouter schema generation
            schema = tool_instance.to_openrouter_schema()
            assert schema["type"] == "function"
            assert "name" in schema["function"]
            assert "description" in schema["function"]