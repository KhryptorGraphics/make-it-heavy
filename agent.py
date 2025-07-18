import json
import yaml
import time
from openai import OpenAI
from tools import discover_tools
from typing import Optional, Dict, Any, List, Union
from openai.types.chat import ChatCompletion
from exceptions import APIError, ToolExecutionError, AgentError, ConfigurationError
from constants import (
    DEFAULT_MAX_ITERATIONS, TOKEN_ESTIMATION_RATIO, AGENT_STATUS_INITIALIZING,
    AGENT_STATUS_RUNNING, AGENT_STATUS_COMPLETED, AGENT_STATUS_FAILED,
    ERROR_INVALID_API_KEY, ERROR_AGENT_MAX_ITERATIONS, SUCCESS_AGENT_INITIALIZED
)

class OpenRouterAgent:
    """OpenRouter Agent with tool integration and agentic loop execution.
    
    This agent connects to OpenRouter's API to execute tasks using available tools.
    It supports both single-shot and iterative execution patterns, with comprehensive
    progress tracking and error handling.
    
    Attributes:
        config (Dict[str, Any]): Configuration loaded from YAML file
        client (OpenAI): OpenRouter API client
        discovered_tools (Dict[str, Any]): Available tools discovered dynamically
        tools (List[Dict[str, Any]]): OpenRouter function calling schema
        tool_mapping (Dict[str, Callable]): Tool name to execution function mapping
        ui_manager (Optional[Any]): UI manager for progress tracking
        agent_id (Optional[str]): Unique identifier for this agent
        silent (bool): Whether to suppress debug output
        metrics (Optional[AgentMetrics]): Performance metrics if UI manager provided
    """
    
    def __init__(self, config_path: str = "config.yaml", silent: bool = False, ui_manager: Optional[Any] = None, agent_id: Optional[str] = None) -> None:
        """Initialize the OpenRouter Agent.
        
        Args:
            config_path: Path to YAML configuration file
            silent: Whether to suppress debug output
            ui_manager: Optional UI manager for progress tracking
            agent_id: Optional unique identifier for this agent
            
        Raises:
            ConfigurationError: If configuration file is invalid or missing
            APIError: If OpenRouter API connection fails
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Silent mode for orchestrator (suppresses debug output)
        self.silent = silent
        
        # UI Manager for enhanced output
        self.ui_manager = ui_manager
        self.agent_id = agent_id or "agent_1"
        
        # Initialize metrics if UI manager provided
        if self.ui_manager:
            max_iterations = self.config.get('agent', {}).get('max_iterations', 10)
            self.metrics = self.ui_manager.create_agent_metrics(self.agent_id, max_iterations)
        
        # Initialize OpenAI client with OpenRouter
        self.client = OpenAI(
            base_url=self.config['openrouter']['base_url'],
            api_key=self.config['openrouter']['api_key']
        )
        
        # Discover tools dynamically
        self.discovered_tools = discover_tools(self.config, silent=self.silent)
        
        # Build OpenRouter tools array
        self.tools = [tool.to_openrouter_schema() for tool in self.discovered_tools.values()]
        
        # Build tool mapping
        self.tool_mapping = {name: tool.execute for name, tool in self.discovered_tools.items()}
    
    
    def call_llm(self, messages: List[Dict[str, Any]]) -> ChatCompletion:
        """Make OpenRouter API call with function calling support.
        
        Args:
            messages: List of chat messages following OpenAI format
            
        Returns:
            ChatCompletion: OpenRouter API response
            
        Raises:
            APIError: If API call fails, with specific error codes for different failures
        """
        try:
            start_time = time.time()
            
            # Update status
            if self.ui_manager:
                self.ui_manager.update_agent_status(self.agent_id, AGENT_STATUS_RUNNING, "Making API call...")
            
            response = self.client.chat.completions.create(
                model=self.config['openrouter']['model'],
                messages=messages,
                tools=self.tools
            )
            
            # Log metrics
            if self.ui_manager:
                elapsed_time = time.time() - start_time
                # Estimate tokens using defined ratio
                total_chars = sum(len(str(msg.get('content', ''))) for msg in messages)
                estimated_tokens = total_chars // TOKEN_ESTIMATION_RATIO
                
                self.ui_manager.log_api_call(self.agent_id, estimated_tokens)
                self.ui_manager.log_timeline(f"Agent {self.agent_id} API call", 
                                           f"Completed in {elapsed_time:.2f}s, ~{estimated_tokens} tokens")
            
            return response
        except Exception as e:
            error_msg = f"LLM call failed: {str(e)}"
            if self.ui_manager:
                self.ui_manager.log_error(self.agent_id, error_msg)
            
            # Check for specific API errors
            if "401" in str(e) or "unauthorized" in str(e).lower():
                raise APIError(ERROR_INVALID_API_KEY, status_code=401)
            elif "timeout" in str(e).lower():
                raise APIError(f"API timeout: {str(e)}", status_code=408)
            else:
                raise APIError(error_msg)
    
    def handle_tool_call(self, tool_call: Any) -> Dict[str, Any]:
        """Execute a tool call and return the result in OpenAI format.
        
        Args:
            tool_call: OpenAI tool call object containing function name and arguments
            
        Returns:
            Dict[str, Any]: Tool result message in OpenAI format
            
        Raises:
            ToolExecutionError: If tool execution fails or tool is not found
        """
        tool_name = tool_call.function.name
        try:
            # Extract tool name and arguments
            tool_args = json.loads(tool_call.function.arguments)
            
            # Update status
            if self.ui_manager:
                self.ui_manager.update_agent_status(self.agent_id, AGENT_STATUS_RUNNING, f"Using tool: {tool_name}")
            
            # Call appropriate tool from tool_mapping
            if tool_name in self.tool_mapping:
                start_time = time.time()
                tool_result = self.tool_mapping[tool_name](**tool_args)
                elapsed_time = time.time() - start_time
                
                # Log successful tool usage
                if self.ui_manager:
                    self.ui_manager.log_tool_usage(self.agent_id, tool_name, True)
                    self.ui_manager.log_timeline(f"Agent {self.agent_id} tool", 
                                               f"Used {tool_name} in {elapsed_time:.2f}s")
            else:
                error_msg = f"Unknown tool: {tool_name}"
                if self.ui_manager:
                    self.ui_manager.log_tool_usage(self.agent_id, tool_name, False)
                raise ToolExecutionError(tool_name, error_msg, tool_args)
            
            # Return tool result message
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(tool_result)
            }
        
        except ToolExecutionError as e:
            # Re-raise tool execution errors
            if self.ui_manager:
                self.ui_manager.log_tool_usage(self.agent_id, tool_name, False)
                self.ui_manager.log_error(self.agent_id, str(e))
            
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps({"error": str(e)})
            }
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            if self.ui_manager:
                self.ui_manager.log_tool_usage(self.agent_id, tool_name, False)
                self.ui_manager.log_error(self.agent_id, error_msg)
            
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps({"error": error_msg})
            }
    
    def run(self, user_input: str) -> str:
        """Execute the agent with user input using an agentic loop.
        
        The agent will iteratively call the LLM and execute tools until either:
        1. The task is completed (mark_task_complete tool is called)
        2. Maximum iterations are reached
        3. An unrecoverable error occurs
        
        Args:
            user_input: User's question or task description
            
        Returns:
            str: Full conversation content from the agent
            
        Raises:
            AgentError: If execution fails or max iterations reached without completion
            APIError: If OpenRouter API calls fail
            ToolExecutionError: If tool execution fails
        """
        # Initialize status
        if self.ui_manager:
            self.ui_manager.update_agent_status(self.agent_id, AGENT_STATUS_RUNNING, "Initializing...")
            self.ui_manager.log_timeline(f"Agent {self.agent_id} started", f"Input: {user_input[:50]}...")
        
        # Initialize conversation
        messages = self._initialize_conversation(user_input)
        full_response_content = []
        
        # Get configuration
        max_iterations = self.config.get('agent', {}).get('max_iterations', DEFAULT_MAX_ITERATIONS)
        iteration = 0
        
        try:
            while iteration < max_iterations:
                iteration += 1
                self._update_iteration_progress(iteration, max_iterations)
                
                # Call LLM
                response = self.call_llm(messages)
                
                # Add the response to messages
                assistant_message = response.choices[0].message
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": assistant_message.tool_calls
                })
                
                # Handle assistant response
                if self._handle_assistant_response(assistant_message, full_response_content):
                    return "\n\n".join(full_response_content)
                
                # Execute tool calls if present
                if assistant_message.tool_calls:
                    self._execute_tool_calls(assistant_message.tool_calls, messages)
            
            # If max iterations reached
            if not full_response_content:
                error_msg = ERROR_AGENT_MAX_ITERATIONS
                if self.ui_manager:
                    self.ui_manager.update_agent_status(self.agent_id, AGENT_STATUS_FAILED, "Max iterations reached")
                    self.ui_manager.agent_failed(self.agent_id, error_msg)
                raise AgentError(error_msg, self.agent_id, max_iterations)
            
            result = "\n\n".join(full_response_content)
            if self.ui_manager:
                self.ui_manager.update_agent_status(self.agent_id, AGENT_STATUS_COMPLETED, "Max iterations reached")
                self.ui_manager.agent_completed(self.agent_id)
            
            return result
            
        except (APIError, ToolExecutionError, AgentError) as e:
            # Handle known errors
            if self.ui_manager:
                self.ui_manager.agent_failed(self.agent_id, str(e))
            
            if not self.silent:
                print(f"❌ {str(e)}")
            
            raise e
        except Exception as e:
            error_msg = f"Unexpected agent error: {str(e)}"
            agent_error = AgentError(error_msg, self.agent_id, iteration)
            
            if self.ui_manager:
                self.ui_manager.agent_failed(self.agent_id, str(agent_error))
            
            if not self.silent:
                print(f"❌ {str(agent_error)}")
            
            raise agent_error
    
    def _initialize_conversation(self, user_input: str) -> List[Dict[str, Any]]:
        """Initialize the conversation with system prompt and user input.
        
        Args:
            user_input: User's question or task description
            
        Returns:
            List[Dict[str, Any]]: Initial conversation messages
        """
        return [
            {
                "role": "system",
                "content": self.config['system_prompt']
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
    
    def _handle_assistant_response(self, assistant_message: Any, full_response_content: List[str]) -> bool:
        """Handle assistant response and capture content.
        
        Args:
            assistant_message: Assistant response from OpenRouter
            full_response_content: List to append response content to
            
        Returns:
            bool: True if task was completed, False otherwise
        """
        # Capture assistant content for full response
        if assistant_message.content:
            full_response_content.append(assistant_message.content)
        
        # Check if there are tool calls
        if assistant_message.tool_calls:
            if not self.silent:
                print(f"🔧 Agent making {len(assistant_message.tool_calls)} tool call(s)")
            
            # Handle each tool call
            task_completed = False
            for tool_call in assistant_message.tool_calls:
                if not self.silent:
                    print(f"   📞 Calling tool: {tool_call.function.name}")
                
                # Check if this was the task completion tool
                if tool_call.function.name == "mark_task_complete":
                    task_completed = True
                    if not self.silent:
                        print("✅ Task completion tool called - exiting loop")
                    
                    # Mark as completed
                    if self.ui_manager:
                        self.ui_manager.agent_completed(self.agent_id)
                    
                    return True
            
            return task_completed
        else:
            if not self.silent:
                print("💭 Agent responded without tool calls - continuing loop")
            
            if self.ui_manager:
                self.ui_manager.update_agent_status(self.agent_id, AGENT_STATUS_RUNNING, "Thinking...")
            
            return False
    
    def _execute_tool_calls(self, tool_calls: List[Any], messages: List[Dict[str, Any]]) -> None:
        """Execute all tool calls and add results to messages.
        
        Args:
            tool_calls: List of tool calls to execute
            messages: Conversation messages to append results to
        """
        for tool_call in tool_calls:
            tool_result = self.handle_tool_call(tool_call)
            messages.append(tool_result)
    
    def _update_iteration_progress(self, iteration: int, max_iterations: int) -> None:
        """Update iteration progress in UI manager.
        
        Args:
            iteration: Current iteration number
            max_iterations: Maximum allowed iterations
        """
        if self.ui_manager:
            self.ui_manager.update_agent_iteration(self.agent_id, iteration)
            self.ui_manager.update_agent_status(self.agent_id, AGENT_STATUS_RUNNING, 
                                              f"Iteration {iteration}/{max_iterations}")
        
        if not self.silent:
            print(f"🔄 Agent iteration {iteration}/{max_iterations}")