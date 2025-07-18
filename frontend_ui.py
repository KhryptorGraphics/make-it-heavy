"""
Frontend-focused UI components for Make It Heavy
Enhanced user experience with modern CLI patterns and accessibility features.
"""

import os
import time
from typing import Dict, List, Optional, Any, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn, TaskProgressColumn, TimeRemainingColumn
from rich.text import Text
from rich import box
from rich.align import Align
from rich.live import Live
from rich.status import Status

from constants import EXIT_COMMANDS


class MessageStyleManager:
    """Consistent message styling system for better visual hierarchy"""
    
    STYLES = {
        'primary': "bold blue",
        'success': "bold green", 
        'warning': "bold yellow",
        'error': "bold red",
        'info': "cyan",
        'muted': "dim white",
        'accent': "magenta",
        'highlight': "bold cyan"
    }
    
    ICONS = {
        'success': "✅",
        'error': "❌",
        'warning': "⚠️",
        'info': "ℹ️",
        'question': "❓",
        'thinking': "🤔",
        'working': "⚙️",
        'celebration': "🎉",
        'rocket': "🚀",
        'magic': "✨"
    }
    
    def __init__(self, console: Console):
        self.console = console
    
    def format_message(self, message: str, level: str, icon: str = None) -> str:
        """Standardized message formatting with consistent styling"""
        style = self.STYLES.get(level, "white")
        icon_str = self.ICONS.get(icon, "") if icon else ""
        prefix = f"{icon_str} " if icon_str else ""
        return f"[{style}]{prefix}{message}[/{style}]"
    
    def print_message(self, message: str, level: str = "info", icon: str = None):
        """Print formatted message with consistent styling"""
        formatted = self.format_message(message, level, icon)
        self.console.print(formatted)
    
    def create_status_panel(self, title: str, content: str, style: str = "blue") -> Panel:
        """Create consistent status panel"""
        return Panel(
            content,
            title=title,
            border_style=style,
            padding=(1, 2)
        )


class UserFriendlyErrorHandler:
    """Convert technical errors to user-friendly messages with actionable guidance"""
    
    ERROR_TRANSLATIONS = {
        'ConnectionError': {
            'user_message': "Unable to connect to the AI service",
            'icon': 'error',
            'suggestions': [
                "Check your internet connection",
                "Verify your API key is correct",
                "Try again in a few moments - the service might be busy"
            ],
            'technical_help': "If this continues, check the OpenRouter status page"
        },
        'TimeoutError': {
            'user_message': "The request took too long to complete",
            'icon': 'warning',
            'suggestions': [
                "Try asking a simpler question",
                "Check your internet connection speed",
                "The AI service might be busy - try again in a moment"
            ],
            'technical_help': "Consider increasing timeout settings in config.yaml"
        },
        'APIError': {
            'user_message': "There was an issue with the AI service",
            'icon': 'error',
            'suggestions': [
                "Check your API key is valid and has credits",
                "Try again - this might be a temporary issue",
                "Switch to a different AI model in settings"
            ],
            'technical_help': "Check the OpenRouter dashboard for account status"
        },
        'ConfigurationError': {
            'user_message': "There's a problem with your configuration",
            'icon': 'warning',
            'suggestions': [
                "Run the setup wizard with 'setup' command",
                "Check that your config.yaml file is valid",
                "Reset to default settings if needed"
            ],
            'technical_help': "Configuration file location: config.yaml"
        },
        'ValidationError': {
            'user_message': "The input provided isn't valid",
            'icon': 'info',
            'suggestions': [
                "Check the format of your input",
                "Try rephrasing your question",
                "Type 'help' for usage examples"
            ],
            'technical_help': "Use 'examples' command to see valid input formats"
        }
    }
    
    def __init__(self, console: Console, style_manager: MessageStyleManager):
        self.console = console
        self.style_manager = style_manager
    
    def handle_error(self, error: Exception, show_technical: bool = False) -> None:
        """Display user-friendly error message with guidance"""
        error_type = type(error).__name__
        error_info = self.ERROR_TRANSLATIONS.get(error_type, {
            'user_message': "Something unexpected happened",
            'icon': 'error',
            'suggestions': [
                "Try again with a different approach",
                "Type 'help' for usage guidance",
                "Contact support if this continues"
            ],
            'technical_help': f"Error: {str(error)}"
        })
        
        # Create error panel
        suggestions_text = "\n".join(f"• {suggestion}" for suggestion in error_info['suggestions'])
        
        content = f"[bold red]{error_info['user_message']}[/bold red]\n\n"
        content += f"[bold]What you can try:[/bold]\n{suggestions_text}"
        
        if show_technical:
            content += f"\n\n[dim]Technical details: {error_info['technical_help']}[/dim]"
        
        error_panel = Panel(
            content,
            title="⚠️ Oops!",
            border_style="red",
            padding=(1, 2)
        )
        
        self.console.print(error_panel)
    
    def show_recovery_suggestions(self, error_type: str) -> None:
        """Show specific recovery suggestions for error types"""
        if error_type in self.ERROR_TRANSLATIONS:
            suggestions = self.ERROR_TRANSLATIONS[error_type]['suggestions']
            self.console.print("\n[bold blue]💡 Quick fixes:[/bold blue]")
            for i, suggestion in enumerate(suggestions, 1):
                self.console.print(f"  {i}. {suggestion}")


class InteractiveInputManager:
    """Enhanced input handling with validation, suggestions, and user guidance"""
    
    COMMAND_SUGGESTIONS = {
        'help': {
            'description': 'Show available commands and usage help',
            'examples': ['help', 'help tools', 'help examples']
        },
        'tools': {
            'description': 'List available tools and their capabilities',
            'examples': ['tools', 'tools search', 'tools calculate']
        },
        'examples': {
            'description': 'Show usage examples for different tasks',
            'examples': ['examples', 'examples search', 'examples math']
        },
        'setup': {
            'description': 'Run the configuration setup wizard',
            'examples': ['setup', 'setup api-key', 'setup model']
        },
        'status': {
            'description': 'Show current system status and configuration',
            'examples': ['status', 'status config', 'status api']
        }
    }
    
    TASK_SUGGESTIONS = {
        'search': {
            'patterns': ['search for', 'find information about', 'look up', 'research'],
            'examples': [
                'Search for information about quantum computing',
                'Find recent news about artificial intelligence',
                'Look up the weather in Tokyo'
            ]
        },
        'calculate': {
            'patterns': ['calculate', 'compute', 'math', 'solve', 'equation'],
            'examples': [
                'Calculate the area of a circle with radius 5',
                'Solve the equation 2x + 3 = 15',
                'What is 15% of 250?'
            ]
        },
        'file': {
            'patterns': ['read file', 'open file', 'show contents', 'file'],
            'examples': [
                'Read the contents of todo.txt',
                'Show me what\'s in the report.pdf file',
                'Open and summarize the data.csv file'
            ]
        },
        'write': {
            'patterns': ['write file', 'create file', 'save to', 'write to'],
            'examples': [
                'Write a summary to summary.txt',
                'Create a new file called notes.md',
                'Save the results to output.json'
            ]
        }
    }
    
    def __init__(self, console: Console, style_manager: MessageStyleManager):
        self.console = console
        self.style_manager = style_manager
    
    def get_user_input(self, context: str = "ask a question") -> str:
        """Interactive input with suggestions and validation"""
        self.show_input_prompt(context)
        
        while True:
            try:
                user_input = Prompt.ask(
                    "[bold cyan]❯[/bold cyan]",
                    default="",
                    show_default=False
                ).strip()
                
                if self.validate_input(user_input):
                    return user_input
                    
            except KeyboardInterrupt:
                self.console.print("\n[yellow]💡 Use 'quit' to exit gracefully[/yellow]")
            except EOFError:
                self.console.print("\n[yellow]Goodbye![/yellow]")
                return "quit"
    
    def show_input_prompt(self, context: str) -> None:
        """Show contextual input prompt with helpful information"""
        self.console.print(f"\n[bold blue]💬 What would you like to do?[/bold blue]")
        self.console.print(f"[dim]You can {context} or type 'help' for options[/dim]")
        
        # Show quick suggestions
        suggestions = self.get_quick_suggestions()
        if suggestions:
            self.console.print(f"[dim]💡 Try: {' | '.join(suggestions)}[/dim]")
    
    def get_quick_suggestions(self) -> List[str]:
        """Get quick suggestion prompts"""
        return [
            "'help' for commands",
            "'examples' for ideas", 
            "'tools' to see capabilities"
        ]
    
    def validate_input(self, input_text: str) -> bool:
        """Validate input and provide helpful suggestions"""
        if not input_text:
            self.console.print("[yellow]💡 Try typing a question or command[/yellow]")
            return False
        
        # Check for common greetings and redirect
        if input_text.lower() in ['hi', 'hello', 'hey', 'yo', 'sup']:
            self.console.print("[yellow]👋 Hello! I'm ready to help. What would you like to do?[/yellow]")
            self.show_quick_examples()
            return False
        
        # Check for single words that might need more context
        if len(input_text.split()) == 1 and input_text.lower() not in ['help', 'tools', 'examples', 'status', 'setup'] + EXIT_COMMANDS:
            self.console.print(f"[yellow]💡 Could you be more specific? Try: 'search for {input_text}' or 'calculate {input_text}'[/yellow]")
            return False
        
        return True
    
    def show_quick_examples(self) -> None:
        """Show quick examples to get users started"""
        examples = [
            "Search for information about space exploration",
            "Calculate 15% of 250",
            "Help me write a professional email"
        ]
        
        self.console.print("\n[bold]Here are some things you can try:[/bold]")
        for example in examples:
            self.console.print(f"  • {example}")
    
    def suggest_completions(self, partial_input: str) -> List[str]:
        """Suggest completions based on partial input"""
        suggestions = []
        partial_lower = partial_input.lower()
        
        # Check command suggestions
        for command, info in self.COMMAND_SUGGESTIONS.items():
            if command.startswith(partial_lower):
                suggestions.append(f"{command} - {info['description']}")
        
        # Check task pattern suggestions
        for task, info in self.TASK_SUGGESTIONS.items():
            for pattern in info['patterns']:
                if pattern.startswith(partial_lower):
                    suggestions.append(pattern)
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def show_context_help(self, input_text: str) -> None:
        """Show contextual help based on input"""
        input_lower = input_text.lower()
        
        if any(pattern in input_lower for pattern in ['search', 'find', 'look up']):
            self.console.print("[dim]💡 I can search the web for current information[/dim]")
        elif any(pattern in input_lower for pattern in ['calculate', 'math', 'solve']):
            self.console.print("[dim]💡 I can perform calculations and solve math problems[/dim]")
        elif any(pattern in input_lower for pattern in ['file', 'read', 'open']):
            self.console.print("[dim]💡 I can read and analyze files for you[/dim]")
        elif any(pattern in input_lower for pattern in ['write', 'create', 'save']):
            self.console.print("[dim]💡 I can write content to files[/dim]")


class HelpSystem:
    """Comprehensive help system with contextual guidance"""
    
    def __init__(self, console: Console, style_manager: MessageStyleManager):
        self.console = console
        self.style_manager = style_manager
    
    def show_main_help(self) -> None:
        """Display main help screen with all available options"""
        # Create main help layout
        layout = Layout()
        layout.split_column(
            Layout(self.create_header(), size=3),
            Layout(self.create_commands_section(), size=12),
            Layout(self.create_examples_section(), size=10),
            Layout(self.create_tips_section(), size=6)
        )
        
        self.console.print(layout)
    
    def create_header(self) -> Panel:
        """Create help header"""
        return Panel(
            Align.center("[bold blue]🚀 Make It Heavy Help[/bold blue]\n[dim]Your AI-powered assistant with multiple capabilities[/dim]"),
            border_style="blue"
        )
    
    def create_commands_section(self) -> Panel:
        """Create commands reference section"""
        commands_table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
        commands_table.add_column("Command", style="cyan", width=12)
        commands_table.add_column("Description", style="white", width=35)
        commands_table.add_column("Example", style="dim", width=20)
        
        commands = [
            ("help", "Show this help message", "help"),
            ("tools", "List available tools", "tools"),
            ("examples", "Show usage examples", "examples"),
            ("setup", "Run configuration wizard", "setup"),
            ("status", "Show system status", "status"),
            ("quit/exit", "Exit the application", "quit")
        ]
        
        for command, description, example in commands:
            commands_table.add_row(command, description, example)
        
        return Panel(commands_table, title="📋 Available Commands", border_style="green")
    
    def create_examples_section(self) -> Panel:
        """Create examples section"""
        examples_content = """
[bold cyan]🔍 Information & Research[/bold cyan]
• Search for information about quantum computing
• Find recent news about artificial intelligence
• Look up the weather in Tokyo

[bold cyan]🧮 Calculations & Math[/bold cyan]
• Calculate the area of a circle with radius 5
• Solve the equation 2x + 3 = 15
• What is 15% of 250?

[bold cyan]📄 File Operations[/bold cyan]
• Read the contents of todo.txt
• Write a summary to summary.txt
• Analyze the data in report.csv
"""
        
        return Panel(examples_content, title="💡 Usage Examples", border_style="yellow")
    
    def create_tips_section(self) -> Panel:
        """Create tips section"""
        tips_content = """
[bold green]✨ Pro Tips[/bold green]
• Be specific in your requests for better results
• Use natural language - no special commands needed
• Type 'status' to check your configuration
• Use 'setup' to reconfigure API settings
"""
        
        return Panel(tips_content, title="🎯 Tips for Success", border_style="magenta")
    
    def show_tool_help(self, tool_name: str = None) -> None:
        """Show detailed help for tools"""
        if tool_name:
            self.show_specific_tool_help(tool_name)
        else:
            self.show_all_tools_help()
    
    def show_all_tools_help(self) -> None:
        """Show help for all available tools"""
        tools_table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        tools_table.add_column("Tool", style="cyan", width=15)
        tools_table.add_column("Description", style="white", width=40)
        tools_table.add_column("Example Usage", style="dim", width=30)
        
        tools = [
            ("search_web", "Search the internet for current information", "Search for Python tutorials"),
            ("calculate", "Perform mathematical calculations", "Calculate 15% of 250"),
            ("read_file", "Read and analyze file contents", "Read my todo.txt file"),
            ("write_file", "Write content to files", "Write summary to notes.txt"),
            ("mark_task_complete", "Mark tasks as finished", "Automatically used when done")
        ]
        
        for tool, description, example in tools:
            tools_table.add_row(tool, description, example)
        
        self.console.print(Panel(
            tools_table,
            title="🛠️ Available Tools",
            border_style="blue"
        ))
    
    def show_specific_tool_help(self, tool_name: str) -> None:
        """Show detailed help for a specific tool"""
        tool_info = self.get_tool_info(tool_name)
        
        if tool_info:
            content = f"""
[bold]{tool_info['name']}[/bold]

[bold cyan]Description:[/bold cyan]
{tool_info['description']}

[bold cyan]How to use:[/bold cyan]
{tool_info['usage']}

[bold cyan]Examples:[/bold cyan]
{chr(10).join(f"• {example}" for example in tool_info['examples'])}
"""
            
            self.console.print(Panel(
                content,
                title=f"🔧 Tool: {tool_name}",
                border_style="blue"
            ))
        else:
            self.console.print(f"[red]Tool '{tool_name}' not found. Use 'tools' to see available tools.[/red]")
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a tool"""
        tool_info = {
            'search_web': {
                'name': 'Web Search',
                'description': 'Search the internet for current information on any topic',
                'usage': 'Just ask me to search for something or find information about a topic',
                'examples': [
                    'Search for information about quantum computing',
                    'Find recent news about artificial intelligence',
                    'Look up the weather in Tokyo'
                ]
            },
            'calculate': {
                'name': 'Calculator',
                'description': 'Perform mathematical calculations and solve equations',
                'usage': 'Ask me to calculate, solve, or compute mathematical problems',
                'examples': [
                    'Calculate the area of a circle with radius 5',
                    'Solve the equation 2x + 3 = 15',
                    'What is 15% of 250?'
                ]
            },
            'read_file': {
                'name': 'File Reader',
                'description': 'Read and analyze the contents of files',
                'usage': 'Ask me to read, open, or analyze a file',
                'examples': [
                    'Read the contents of todo.txt',
                    'Show me what\'s in the report.pdf file',
                    'Analyze the data in spreadsheet.csv'
                ]
            },
            'write_file': {
                'name': 'File Writer',
                'description': 'Write content to files',
                'usage': 'Ask me to write, create, or save content to a file',
                'examples': [
                    'Write a summary to summary.txt',
                    'Create a new file called notes.md',
                    'Save the results to output.json'
                ]
            }
        }
        
        return tool_info.get(tool_name)
    
    def show_examples(self, category: str = None) -> None:
        """Show usage examples by category"""
        if category:
            self.show_category_examples(category)
        else:
            self.show_all_examples()
    
    def show_all_examples(self) -> None:
        """Show all usage examples organized by category"""
        categories = {
            "🔍 Research & Information": [
                "Search for information about renewable energy",
                "Find recent developments in space exploration",
                "Look up historical events from the 1960s",
                "Research the benefits of meditation"
            ],
            "🧮 Math & Calculations": [
                "Calculate compound interest on $1000 at 5% for 10 years",
                "Solve for x: 3x + 7 = 22",
                "What's the area of a rectangle 12m by 8m?",
                "Convert 75 degrees Fahrenheit to Celsius"
            ],
            "📄 File Operations": [
                "Read my shopping list from groceries.txt",
                "Analyze the sales data in report.csv",
                "Summarize the contents of meeting-notes.pdf",
                "Create a new file with project ideas"
            ],
            "✍️ Writing & Creation": [
                "Write a professional email about project updates",
                "Create a summary of today's meetings",
                "Help me write a cover letter for a job application",
                "Generate ideas for a blog post about technology"
            ]
        }
        
        for category, examples in categories.items():
            self.console.print(f"\n[bold]{category}[/bold]")
            for example in examples:
                self.console.print(f"  • {example}")
    
    def show_category_examples(self, category: str) -> None:
        """Show examples for a specific category"""
        category_examples = {
            'search': [
                "Search for information about quantum computing",
                "Find recent news about artificial intelligence",
                "Look up the weather in Tokyo",
                "Research the history of the internet"
            ],
            'math': [
                "Calculate 15% of 250",
                "Solve the equation 2x + 3 = 15",
                "What's the area of a circle with radius 7?",
                "Convert 100 km to miles"
            ],
            'file': [
                "Read the contents of todo.txt",
                "Analyze the data in report.csv",
                "Show me what's in the config file",
                "Summarize the document.pdf file"
            ],
            'write': [
                "Write a summary to notes.txt",
                "Create a new file called ideas.md",
                "Save the results to output.json",
                "Write a professional email draft"
            ]
        }
        
        examples = category_examples.get(category.lower(), [])
        if examples:
            self.console.print(f"\n[bold cyan]Examples for {category}:[/bold cyan]")
            for example in examples:
                self.console.print(f"  • {example}")
        else:
            self.console.print(f"[red]No examples found for category '{category}'[/red]")


class WelcomeScreen:
    """Enhanced welcome screen with better onboarding"""
    
    def __init__(self, console: Console, style_manager: MessageStyleManager):
        self.console = console
        self.style_manager = style_manager
    
    def show_welcome(self, mode: str = "single") -> None:
        """Show enhanced welcome screen with onboarding"""
        self.console.clear()
        
        # Create welcome layout
        layout = Layout()
        layout.split_column(
            Layout(self.create_header(mode), size=5),
            Layout(self.create_features_section(), size=8),
            Layout(self.create_quick_start_section(), size=6),
            Layout(self.create_footer(), size=3)
        )
        
        self.console.print(layout)
    
    def create_header(self, mode: str) -> Panel:
        """Create welcome header"""
        mode_text = "Single Agent Mode" if mode == "single" else "Grok Heavy Mode"
        mode_desc = "One powerful AI assistant" if mode == "single" else "Four AI agents working together"
        
        header_content = f"""
[bold blue]🚀 Welcome to Make It Heavy![/bold blue]

[bold]{mode_text}[/bold] - {mode_desc}
Your AI-powered assistant with multiple capabilities
"""
        
        return Panel(
            Align.center(header_content),
            border_style="blue"
        )
    
    def create_features_section(self) -> Panel:
        """Create features overview section"""
        features = [
            ("🔍", "Web Search", "Find current information on any topic"),
            ("🧮", "Calculator", "Solve math problems and equations"),
            ("📄", "File Operations", "Read and write files"),
            ("✍️", "Content Creation", "Write and generate content"),
            ("🤖", "AI Assistant", "Natural language conversation")
        ]
        
        features_table = Table(box=box.SIMPLE, show_header=False)
        features_table.add_column("Icon", width=3)
        features_table.add_column("Feature", style="bold cyan", width=15)
        features_table.add_column("Description", style="dim", width=40)
        
        for icon, feature, description in features:
            features_table.add_row(icon, feature, description)
        
        return Panel(features_table, title="✨ What I Can Do", border_style="green")
    
    def create_quick_start_section(self) -> Panel:
        """Create quick start section"""
        quick_start_content = """
[bold cyan]🚀 Quick Start[/bold cyan]
• Just type your question or request in natural language
• Type [bold]'help'[/bold] to see all available commands
• Type [bold]'examples'[/bold] to see what you can ask me
• Type [bold]'quit'[/bold] to exit when you're done

[bold green]💡 First time?[/bold green] Try: "Search for information about artificial intelligence"
"""
        
        return Panel(quick_start_content, title="🎯 Getting Started", border_style="yellow")
    
    def create_footer(self) -> Panel:
        """Create footer with helpful information"""
        footer_content = "[dim]Ready to help! Type your question or command below.[/dim]"
        return Panel(Align.center(footer_content), border_style="dim")
    
    def show_first_time_setup_prompt(self) -> bool:
        """Show first-time setup prompt"""
        self.console.print("\n[bold yellow]🔧 First Time Setup[/bold yellow]")
        self.console.print("It looks like this is your first time using Make It Heavy!")
        self.console.print("Would you like to run the setup wizard to configure your API key?")
        
        return Confirm.ask("\n[bold]Run setup wizard now?[/bold]", default=True)
    
    def check_configuration(self) -> bool:
        """Check if configuration is needed"""
        try:
            # Check if config file exists and has valid API key
            import yaml
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            api_key = config.get('openrouter', {}).get('api_key', '')
            
            # Check for placeholder values
            if not api_key or api_key in ['YOUR KEY', 'YOUR_KEY', 'REPLACE_ME']:
                return False
            
            return True
        except Exception:
            return False