"""
Constants for Make It Heavy
Centralized configuration of magic numbers, strings, and other constants.
"""

# Agent Configuration
DEFAULT_MAX_ITERATIONS = 10
DEFAULT_CONFIG_PATH = "config.yaml"
TOKEN_ESTIMATION_RATIO = 4  # Rough approximation: 1 token = 4 characters

# API Configuration
DEFAULT_API_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0

# UI Configuration
DEFAULT_PROGRESS_REFRESH_RATE = 4  # Times per second
DEFAULT_PROGRESS_UPDATE_INTERVAL = 0.25  # Seconds
DEFAULT_DASHBOARD_TIMEOUT = 600.0  # Seconds for orchestrator dashboard
DEFAULT_SINGLE_AGENT_TIMEOUT = 300.0  # Seconds for single agent progress

# Timeline Configuration
DEFAULT_MAX_TIMELINE_EVENTS = 10

# Tool Configuration
DEFAULT_SEARCH_TIMEOUT = 10  # Seconds
DEFAULT_SEARCH_RESULTS = 5
DEFAULT_CONTENT_TRUNCATION = 1000  # Characters
DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; Make It Heavy Agent)"

# File Operations
DEFAULT_FILE_ENCODING = "utf-8"
DEFAULT_READ_CHUNK_SIZE = 8192

# Orchestrator Configuration
DEFAULT_TASK_TIMEOUT = 300  # Seconds per agent
DEFAULT_PARALLEL_AGENTS = 4
DEFAULT_AGGREGATION_STRATEGY = "consensus"

# Status Values
AGENT_STATUS_INITIALIZING = "initializing"
AGENT_STATUS_RUNNING = "running"
AGENT_STATUS_COMPLETED = "completed"
AGENT_STATUS_FAILED = "failed"

ORCHESTRATOR_PHASE_INITIALIZING = "initializing"
ORCHESTRATOR_PHASE_GENERATING_QUESTIONS = "generating_questions"
ORCHESTRATOR_PHASE_RUNNING_AGENTS = "running_agents"
ORCHESTRATOR_PHASE_SYNTHESIZING = "synthesizing"
ORCHESTRATOR_PHASE_COMPLETED = "completed"
ORCHESTRATOR_PHASE_FAILED = "failed"

# Log Levels
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"

# Exit Commands
EXIT_COMMANDS = ["quit", "exit", "bye"]

# OpenRouter Configuration
DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MINIMUM_CONTEXT_WINDOW = 200000  # 200k tokens recommended

# Error Messages
ERROR_INVALID_API_KEY = "Invalid OpenRouter API key. Please check your configuration."
ERROR_MISSING_DEPENDENCIES = "Missing required dependencies. Please run: pip install -r requirements.txt"
ERROR_INVALID_CONFIG = "Invalid configuration file. Please check config.yaml format."
ERROR_TOOL_NOT_FOUND = "Tool not found in available tools."
ERROR_AGENT_MAX_ITERATIONS = "Agent reached maximum iterations without completion."
ERROR_ORCHESTRATION_TIMEOUT = "Orchestration timeout. Some agents may have failed."

# Success Messages
SUCCESS_AGENT_INITIALIZED = "Agent initialized successfully!"
SUCCESS_ORCHESTRATION_COMPLETE = "Orchestration completed successfully!"
SUCCESS_TOOL_EXECUTED = "Tool executed successfully"

# Info Messages
INFO_AGENT_ITERATION = "Agent iteration {iteration}/{max_iterations}"
INFO_TOOL_EXECUTION = "Executing tool: {tool_name}"
INFO_ORCHESTRATION_START = "Starting multi-agent orchestration"
INFO_SYNTHESIS_START = "Starting response synthesis"

# Warning Messages
WARNING_API_KEY_NEEDED = "Note: Make sure to set your OpenRouter API key in config.yaml"
WARNING_LOW_CONTEXT_WINDOW = "Warning: Model context window may be too small for synthesis"
WARNING_RETRY_ATTEMPT = "Retrying failed operation (attempt {retry_count}/{max_retries})"