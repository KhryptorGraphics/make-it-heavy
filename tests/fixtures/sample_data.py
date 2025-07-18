"""
Sample data fixtures for testing.
Provides realistic test data for various test scenarios.
"""

# Sample user inputs for testing
SAMPLE_USER_INPUTS = [
    "What is artificial intelligence?",
    "How does machine learning work?", 
    "Explain neural networks",
    "What are the applications of AI in healthcare?",
    "Compare supervised and unsupervised learning",
    "Calculate the square root of 144",
    "Write a summary of renewable energy sources",
    "Search for information about quantum computing"
]

# Sample API responses
SAMPLE_API_RESPONSES = {
    "simple_response": {
        "choices": [{
            "message": {
                "content": "This is a simple AI response to the user's question.",
                "tool_calls": None
            }
        }]
    },
    
    "tool_call_response": {
        "choices": [{
            "message": {
                "content": "I'll help you with that calculation.",
                "tool_calls": [{
                    "id": "call_123",
                    "function": {
                        "name": "calculate",
                        "arguments": '{"expression": "sqrt(144)"}'
                    }
                }]
            }
        }]
    },
    
    "completion_response": {
        "choices": [{
            "message": {
                "content": None,
                "tool_calls": [{
                    "id": "call_complete",
                    "function": {
                        "name": "mark_task_complete",
                        "arguments": '{"summary": "Task completed successfully"}'
                    }
                }]
            }
        }]
    }
}

# Sample tool execution results
SAMPLE_TOOL_RESULTS = {
    "calculator_success": {
        "result": 12,
        "expression": "sqrt(144)",
        "success": True
    },
    
    "calculator_error": {
        "error": "Invalid expression: cannot evaluate 'invalid_expr'",
        "expression": "invalid_expr"
    },
    
    "search_results": {
        "query": "artificial intelligence",
        "results": [
            {
                "title": "What is Artificial Intelligence?",
                "url": "https://example.com/ai-intro",
                "snippet": "AI is the simulation of human intelligence..."
            },
            {
                "title": "AI Applications in Modern Technology", 
                "url": "https://example.com/ai-applications",
                "snippet": "AI is used in various fields including..."
            }
        ]
    },
    
    "file_read_success": {
        "content": "Sample file content\nLine 2\nLine 3",
        "file_path": "/path/to/file.txt",
        "lines_read": 3
    },
    
    "file_write_success": {
        "success": True,
        "file_path": "/path/to/output.txt",
        "bytes_written": 25
    }
}

# Sample orchestrator questions
SAMPLE_GENERATED_QUESTIONS = [
    [
        "What are the fundamental concepts of artificial intelligence?",
        "What are the current applications of AI in industry?",
        "What are the ethical considerations surrounding AI?", 
        "What is the future outlook for AI development?"
    ],
    [
        "How do machine learning algorithms process data?",
        "What are the different types of machine learning?"
    ],
    [
        "What are the mathematical foundations of neural networks?",
        "How are neural networks trained and optimized?"
    ]
]

# Sample agent responses for synthesis
SAMPLE_AGENT_RESPONSES = [
    {
        "agent_id": 0,
        "status": "completed",
        "response": "AI fundamentals include machine learning, natural language processing, computer vision, and robotics. These technologies enable computers to perform tasks that typically require human intelligence.",
        "execution_time": 2.5
    },
    {
        "agent_id": 1, 
        "status": "completed",
        "response": "Current AI applications span healthcare (diagnostic imaging), finance (fraud detection), transportation (autonomous vehicles), and entertainment (recommendation systems).",
        "execution_time": 3.1
    },
    {
        "agent_id": 2,
        "status": "completed", 
        "response": "AI ethics involves considerations of bias, privacy, job displacement, accountability, and the need for transparent and explainable AI systems.",
        "execution_time": 2.8
    },
    {
        "agent_id": 3,
        "status": "failed",
        "response": "Agent timeout: Request exceeded maximum execution time",
        "execution_time": 10.0
    }
]

# Sample synthesized responses
SAMPLE_SYNTHESIZED_RESPONSES = [
    "Artificial Intelligence encompasses multiple technologies including machine learning, natural language processing, and computer vision. Current applications span healthcare, finance, and transportation, while ethical considerations around bias, privacy, and accountability remain important challenges for the field.",
    
    "Machine learning processes data through algorithms that can identify patterns and make predictions. The main types include supervised learning (with labeled data), unsupervised learning (finding hidden patterns), and reinforcement learning (learning through trial and error).",
    
    "Neural networks are mathematical models inspired by biological neurons, using weighted connections and activation functions. They are trained through backpropagation, adjusting weights to minimize error between predicted and actual outputs."
]

# Sample configuration variations for testing
SAMPLE_CONFIGS = {
    "minimal": {
        "openrouter": {
            "api_key": "sk-test-key",
            "base_url": "https://openrouter.ai/api/v1",
            "model": "test/model"
        },
        "agent": {"max_iterations": 3},
        "orchestrator": {"parallel_agents": 2, "task_timeout": 10}
    },
    
    "full_features": {
        "openrouter": {
            "api_key": "sk-test-key-full",
            "base_url": "https://openrouter.ai/api/v1", 
            "model": "advanced/model"
        },
        "agent": {"max_iterations": 10},
        "orchestrator": {
            "parallel_agents": 4,
            "task_timeout": 300,
            "aggregation_strategy": "consensus"
        },
        "ui": {
            "rich_output": True,
            "show_progress": True,
            "show_metrics": True
        },
        "performance": {
            "max_concurrent_agents": 4,
            "api_timeout": 30,
            "retry_failed_calls": True
        }
    }
}

# Sample error scenarios
SAMPLE_ERROR_SCENARIOS = {
    "api_unauthorized": {
        "error_type": "APIError",
        "status_code": 401,
        "message": "Unauthorized: Invalid API key"
    },
    
    "api_timeout": {
        "error_type": "APIError", 
        "status_code": 408,
        "message": "Request timeout: API call exceeded time limit"
    },
    
    "tool_execution_error": {
        "error_type": "ToolExecutionError",
        "tool_name": "calculate",
        "message": "Invalid mathematical expression"
    },
    
    "orchestration_error": {
        "error_type": "OrchestrationError",
        "phase": "synthesis",
        "message": "Failed to synthesize agent responses"
    }
}

# Performance test data
PERFORMANCE_TEST_DATA = {
    "concurrent_requests": [
        f"Query {i}: What is the impact of AI on field {i}?"
        for i in range(10)
    ],
    
    "large_responses": [
        "A" * 10000,  # 10KB response
        "B" * 50000,  # 50KB response  
        "C" * 100000, # 100KB response
    ],
    
    "complex_calculations": [
        "((2**10) * 3) + (sqrt(256) / 4)",
        "sum([i**2 for i in range(100)])",
        "factorial(10) / (2**5)"
    ]
}