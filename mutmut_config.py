"""
Configuration for mutation testing with mutmut.
Defines which files to mutate and what mutations to apply.
"""

def pre_mutation(context):
    """Called before each mutation is applied."""
    # Skip mutations in test files
    if 'test' in context.filename:
        context.skip = True
    
    # Skip mutations in configuration files
    if 'config' in context.filename.lower():
        context.skip = True
    
    # Skip mutations in __init__ files
    if '__init__.py' in context.filename:
        context.skip = True


def post_mutation(context):
    """Called after each mutation test completes."""
    pass


# Files to include in mutation testing
PATHS_TO_MUTATE = [
    'agent.py',
    'orchestrator.py', 
    'utils.py',
    'exceptions.py',
    'constants.py',
    'tools/base_tool.py',
    'tools/calculator_tool.py',
    'tools/search_tool.py',
    'tools/read_file_tool.py',
    'tools/write_file_tool.py',
    'tools/task_done_tool.py'
]

# Test command to run for each mutation
TEST_COMMAND = 'pytest tests/unit/ tests/integration/ -x --tb=no -q'

# Mutations to apply
MUTATION_TYPES = [
    'string',      # String literal mutations
    'number',      # Number literal mutations  
    'operator',    # Operator mutations
    'keyword',     # Keyword mutations
    'decorator',   # Decorator mutations
]

# Coverage threshold - mutations below this coverage will be skipped
COVERAGE_THRESHOLD = 80