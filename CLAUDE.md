# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Make It Heavy** is a multi-agent AI framework that emulates Grok Heavy functionality using OpenRouter's API. The system can run in two modes:
1. **Single Agent Mode**: One agent with full tool access for simple tasks
2. **Grok Heavy Mode**: 4 parallel agents with AI-generated questions and synthesis

## Development Commands

### Setup
```bash
# Create virtual environment (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt

# Configure API key in config.yaml
# Replace "YOUR KEY" with actual OpenRouter API key
```

### Running the Application
```bash
# Single agent mode with enhanced CLI
uv run main.py
# or
python main.py

# Multi-agent orchestration (Grok Heavy mode) with real-time dashboard
uv run make_it_heavy.py
# or
python make_it_heavy.py
```

### Enhanced CLI Features
- **Real-time progress tracking** for all operations
- **Rich terminal output** with colors, progress bars, and status indicators
- **Live metrics dashboard** showing API calls, tokens used, and execution time
- **Timeline view** of all operations with timestamps
- **Agent status monitoring** with individual progress tracking
- **Performance summaries** at completion

### Testing
⚠️ **No testing framework currently configured**. The project lacks:
- Unit tests
- Integration tests
- Test runners (pytest, unittest)

### Code Quality
⚠️ **No linting or formatting tools configured**. Missing:
- Linting (flake8, ruff, pylint)
- Formatting (black, autopep8)
- Type checking (mypy)

## Architecture

### Core Components

1. **Agent System** (`agent.py`):
   - `OpenRouterAgent`: Main agent class with agentic loop
   - Tool discovery and execution
   - OpenRouter API integration
   - **Enhanced with real-time progress tracking and metrics**
   - Configurable via `config.yaml`

2. **Orchestrator** (`orchestrator.py`):
   - `TaskOrchestrator`: Manages parallel agents
   - AI-driven question generation
   - Result synthesis
   - **Real-time dashboard integration**
   - Progress tracking with threading

3. **UI Manager** (`ui_manager.py`):
   - `UIManager`: Rich terminal interface with progress tracking
   - `AgentMetrics`: Individual agent performance tracking
   - `OrchestratorMetrics`: System-level metrics
   - Real-time dashboards with live updates
   - Timeline tracking and error reporting

4. **Tool System** (`tools/`):
   - Hot-swappable plugin architecture
   - Auto-discovery via `__init__.py`
   - All tools inherit from `BaseTool`
   - OpenRouter function calling schema

### Key Patterns

- **Plugin Architecture**: Tools are automatically discovered and loaded
- **Agentic Loop**: Agents continue until task completion (`mark_task_complete`)
- **Parallel Execution**: ThreadPoolExecutor for concurrent agents
- **Configuration-Driven**: All behavior controlled via `config.yaml`

### Available Tools

| Tool | File | Purpose |
|------|------|---------|
| `search_web` | `search_tool.py` | DuckDuckGo web search |
| `calculate` | `calculator_tool.py` | Safe math calculations |
| `read_file` | `read_file_tool.py` | File reading with head/tail |
| `write_file` | `write_file_tool.py` | File creation/overwriting |
| `mark_task_complete` | `task_done_tool.py` | Task completion signaling |

## Configuration

### Key Settings (`config.yaml`)

```yaml
openrouter:
  model: "moonshotai/kimi-k2"  # High context window required (200k+ tokens)
  
agent:
  max_iterations: 10  # Prevent infinite loops
  
orchestrator:
  parallel_agents: 4  # Number of concurrent agents
  task_timeout: 300   # Timeout per agent (seconds)

# Enhanced UI and monitoring settings
ui:
  rich_output: true              # Enable rich terminal output
  show_progress: true            # Show real-time progress
  show_metrics: true             # Display performance metrics
  show_timeline: true            # Show operation timeline
  progress_update_frequency: 4   # Updates per second

logging:
  enabled: true                  # Enable structured logging
  level: "INFO"                  # Log level
  include_timestamps: true       # Add timestamps to output

performance:
  max_concurrent_agents: 4       # Maximum parallel agents
  api_timeout: 30                # API call timeout
  retry_failed_calls: true       # Retry failed operations
```

### Model Requirements
- **Context Window**: 200k+ tokens recommended for synthesis
- **Function Calling**: Must support OpenRouter tool calling
- **Concurrent Usage**: Ensure API plan supports parallel requests

## Development Guidelines

### Adding New Tools
1. Create file in `tools/` directory
2. Inherit from `BaseTool`
3. Implement required methods: `name`, `description`, `parameters`, `execute`
4. Tools are automatically discovered on startup

### Tool Development Pattern
```python
from .base_tool import BaseTool

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property
    def description(self) -> str:
        return "Description for function calling"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "Parameter description"}
            },
            "required": ["param"]
        }
    
    def execute(self, param: str) -> dict:
        return {"result": "success"}
```

### Agent Behavior
- Agents run in agentic loops until `mark_task_complete` is called
- Maximum iterations prevent infinite loops
- Silent mode available for orchestrator agents
- Tool calls are handled via OpenRouter function calling

### Orchestrator Flow
1. AI generates specialized questions from user input
2. Questions distributed to parallel agents
3. Agents run independently with tool access
4. Results synthesized by dedicated synthesis agent
5. Final comprehensive answer returned

## Common Issues

### API Configuration
- Ensure valid OpenRouter API key in `config.yaml`
- Check model availability and context limits
- Verify concurrent request limits

### Tool Loading
- Tools must inherit from `BaseTool`
- All required methods must be implemented
- Check `__init__.py` for discovery logic

### Performance
- Increase `task_timeout` for complex tasks
- Adjust `parallel_agents` based on API limits
- Monitor token usage for synthesis operations

## Dependencies

### Core Requirements
- `openai`: OpenRouter API client
- `pyyaml`: Configuration management
- `requests`: HTTP requests for tools
- `beautifulsoup4`: Web scraping
- `ddgs`: DuckDuckGo search

### Python Version
- Requires Python 3.8+
- Tested with uv package manager

## Security Considerations

⚠️ **Current Security Issues**:
- API key stored in plain text in `config.yaml`
- No input validation for tool parameters
- No rate limiting or usage monitoring
- File operations allow arbitrary paths

**Recommendations**:
- Use environment variables for API keys
- Implement input sanitization for tools
- Add path validation for file operations
- Consider API key rotation