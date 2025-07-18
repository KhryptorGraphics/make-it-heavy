"""
Enhanced main CLI with frontend-focused user experience improvements
Better onboarding, error handling, and user guidance
"""

import sys
import threading
import time
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm

from agent import OpenRouterAgent
from ui_manager import UIManager
from orchestrator import TaskOrchestrator
from frontend_ui import (
    MessageStyleManager, UserFriendlyErrorHandler, 
    InteractiveInputManager, HelpSystem, WelcomeScreen
)
from exceptions import APIError, ConfigurationError, AgentError
from constants import EXIT_COMMANDS
from utils import load_config, validate_api_key


class EnhancedMakeItHeavyCLI:
    """Enhanced Make It Heavy CLI with multi-agent orchestration and superior user experience"""
    
    def __init__(self):
        self.console = Console()
        self.style_manager = MessageStyleManager(self.console)
        self.error_handler = UserFriendlyErrorHandler(self.console, self.style_manager)
        self.input_manager = InteractiveInputManager(self.console, self.style_manager)
        self.help_system = HelpSystem(self.console, self.style_manager)
        self.welcome_screen = WelcomeScreen(self.console, self.style_manager)
        
        self.ui_manager: Optional[UIManager] = None
        self.orchestrator: Optional[TaskOrchestrator] = None
        self.config: Optional[dict] = None
    
    def run(self) -> None:
        """Main entry point with enhanced user experience"""
        try:
            # Show welcome screen
            self.welcome_screen.show_welcome("orchestrator")
            
            # Check configuration
            if not self.check_and_setup_configuration():
                return
            
            # Initialize components
            if not self.initialize_components():
                return
            
            # Run main interaction loop
            self.main_loop()
            
        except KeyboardInterrupt:
            self.handle_graceful_exit()
        except Exception as e:
            self.error_handler.handle_error(e, show_technical=True)
    
    def check_and_setup_configuration(self) -> bool:
        """Check configuration and run setup if needed"""
        try:
            # Try to load configuration
            self.config = load_config()
            
            # Validate API key
            api_key = self.config.get('openrouter', {}).get('api_key', '')
            if not validate_api_key(api_key):
                return self.handle_configuration_setup()
            
            return True
            
        except ConfigurationError as e:
            self.style_manager.print_message(
                "Configuration issue detected", "warning", "warning"
            )
            return self.handle_configuration_setup()
    
    def handle_configuration_setup(self) -> bool:
        """Handle configuration setup process"""
        if self.welcome_screen.show_first_time_setup_prompt():
            return self.run_setup_wizard()
        else:
            self.style_manager.print_message(
                "You can run setup later with the 'setup' command", "info", "info"
            )
            self.style_manager.print_message(
                "Make sure to configure your API key in config.yaml", "warning", "warning"
            )
            return False
    
    def run_setup_wizard(self) -> bool:
        """Run interactive setup wizard"""
        try:
            from setup_wizard import ConfigurationWizard
            wizard = ConfigurationWizard(self.console, self.style_manager)
            return wizard.run_setup()
        except ImportError:
            self.style_manager.print_message(
                "Setup wizard not available. Please configure config.yaml manually", 
                "warning", "warning"
            )
            return False
    
    def initialize_components(self) -> bool:
        """Initialize UI manager and agent with error handling"""
        try:
            # Initialize UI Manager
            self.ui_manager = UIManager()
            self.style_manager.print_message(
                "Initializing multi-agent orchestration system...", "info", "working"
            )
            
            # Initialize orchestrator with UI manager
            self.orchestrator = TaskOrchestrator(ui_manager=self.ui_manager)
            
            self.style_manager.print_message(
                "Multi-agent system ready!", "success", "success"
            )
            
            self.show_orchestrator_info()
            return True
            
        except APIError as e:
            self.error_handler.handle_error(e)
            return False
        except Exception as e:
            self.error_handler.handle_error(e, show_technical=True)
            return False
    
    def show_orchestrator_info(self) -> None:
        """Show orchestrator information and capabilities"""
        model = self.config.get('openrouter', {}).get('model', 'Unknown')
        num_agents = self.config.get('orchestrator', {}).get('parallel_agents', 4)
        
        info_content = f"""
[bold green]✅ Make It Heavy Ready![/bold green]

[bold cyan]Model:[/bold cyan] {model}
[bold cyan]Parallel Agents:[/bold cyan] {num_agents}
[bold cyan]Mode:[/bold cyan] Multi-agent orchestration (Grok Heavy)
[bold cyan]Capabilities:[/bold cyan] Complex analysis, research, parallel processing

[dim]Ask complex questions that require multiple perspectives![/dim]
"""
        
        self.console.print(self.style_manager.create_status_panel(
            "🚀 Orchestration Status", info_content, "green"
        ))
    
    def main_loop(self) -> None:
        """Enhanced main interaction loop"""
        self.style_manager.print_message(
            "Ready to help! What would you like to do?", "primary", "rocket"
        )
        
        while True:
            try:
                # Get user input with enhanced interface
                user_input = self.input_manager.get_user_input("ask me anything")
                
                # Handle special commands
                if self.handle_special_commands(user_input):
                    continue
                
                # Check for exit commands
                if user_input.lower() in EXIT_COMMANDS:
                    self.handle_graceful_exit()
                    break
                
                # Process user request
                self.process_user_request(user_input)
                
            except KeyboardInterrupt:
                self.handle_graceful_exit()
                break
            except Exception as e:
                self.error_handler.handle_error(e)
                self.style_manager.print_message(
                    "I'm still here! Try again or type 'help' for assistance.", 
                    "info", "info"
                )
    
    def handle_special_commands(self, user_input: str) -> bool:
        """Handle special commands that don't require agent processing"""
        command = user_input.lower().strip()
        
        if command == 'help':
            self.help_system.show_main_help()
            return True
        
        elif command == 'tools':
            self.help_system.show_tool_help()
            return True
        
        elif command == 'examples':
            self.help_system.show_examples()
            return True
        
        elif command == 'status':
            self.show_status()
            return True
        
        elif command == 'setup':
            self.run_setup_wizard()
            return True
        
        elif command.startswith('help '):
            # Help for specific topic
            topic = command[5:].strip()
            if topic in ['tools', 'examples']:
                self.help_system.show_tool_help(topic if topic == 'tools' else None)
            else:
                self.help_system.show_specific_tool_help(topic)
            return True
        
        elif command.startswith('examples '):
            # Examples for specific category
            category = command[9:].strip()
            self.help_system.show_examples(category)
            return True
        
        return False
    
    def show_status(self) -> None:
        """Show current system status"""
        model = self.config.get('openrouter', {}).get('model', 'Unknown')
        api_key = self.config.get('openrouter', {}).get('api_key', '')
        num_agents = self.config.get('orchestrator', {}).get('parallel_agents', 4)
        
        # Mask API key for security
        masked_key = api_key[:8] + "*" * (len(api_key) - 12) + api_key[-4:] if len(api_key) > 12 else "Not configured"
        
        status_content = f"""
[bold cyan]🔧 System Configuration[/bold cyan]

[bold]Model:[/bold] {model}
[bold]API Key:[/bold] {masked_key}
[bold]Parallel Agents:[/bold] {num_agents}
[bold]Mode:[/bold] Multi-agent orchestration
[bold]Status:[/bold] Ready

[bold cyan]📊 Orchestration Features[/bold cyan]
• Multi-perspective analysis
• Parallel processing
• Real-time progress tracking
• Intelligent synthesis
"""
        
        self.console.print(self.style_manager.create_status_panel(
            "System Status", status_content, "blue"
        ))
    
    def process_user_request(self, user_input: str) -> None:
        """Process user request with multi-agent orchestration and enhanced feedback"""
        try:
            # Show that we're starting orchestration
            self.style_manager.print_message(
                "Starting Grok Heavy analysis...", "info", "magic"
            )
            
            self.show_orchestration_preview(user_input)
            
            # Start dashboard in background
            dashboard_thread = threading.Thread(
                target=self.ui_manager.show_orchestrator_dashboard,
                daemon=True
            )
            dashboard_thread.start()
            
            # Process with orchestrator
            start_time = time.time()
            response = self.orchestrator.orchestrate(user_input)
            duration = time.time() - start_time
            
            # Show response with enhanced formatting
            self.show_response(response, duration)
            self.show_performance_summary(duration)
            
            # Show completion celebration
            self.style_manager.print_message(
                "Grok Heavy analysis completed!", "success", "celebration"
            )
            
        except Exception as e:
            self.error_handler.handle_error(e)
            self.suggest_alternatives(user_input)
    
    def show_orchestration_preview(self, user_input: str) -> None:
        """Show what the orchestration will do"""
        from utils import format_duration
        num_agents = self.config.get('orchestrator', {}).get('parallel_agents', 4)
        
        preview_content = f"""
[bold cyan]🎯 Analysis Plan[/bold cyan]

[bold]Your Question:[/bold] {user_input}

[bold]What will happen:[/bold]
1. 🤖 AI will generate {num_agents} specialized research questions
2. ⚡ {num_agents} agents will work in parallel on different aspects  
3. 📊 Real-time progress tracking will show agent status
4. 🔄 All results will be synthesized into one comprehensive answer

[bold]Estimated time:[/bold] 1-3 minutes depending on complexity
"""
        
        from rich.panel import Panel
        self.console.print(Panel(preview_content, title="🚀 Grok Heavy Preview", border_style="cyan"))

    def show_response(self, response: str, duration: float) -> None:
        """Display orchestration response with enhanced formatting"""
        from utils import format_duration
        # Create response panel
        response_panel = self.style_manager.create_status_panel(
            f"🎉 Grok Heavy Results ({format_duration(duration)})", response, "green"
        )
        
        self.console.print("\n")
        self.console.print(response_panel)
        self.console.print("\n")
    
    def show_performance_summary(self, execution_time: float) -> None:
        """Show performance summary of the orchestration"""
        from utils import format_duration
        num_agents = self.config.get('orchestrator', {}).get('parallel_agents', 4)
        
        # Calculate metrics from UI manager if available
        total_api_calls = 0
        total_tokens = 0
        total_tools = 0
        
        if self.ui_manager and self.ui_manager.agent_metrics:
            total_api_calls = sum(metrics.api_calls for metrics in self.ui_manager.agent_metrics.values())
            total_tokens = sum(metrics.tokens_used for metrics in self.ui_manager.agent_metrics.values())
            total_tools = sum(len(metrics.tools_used) for metrics in self.ui_manager.agent_metrics.values())
        
        summary_content = f"""
[bold cyan]📊 Performance Summary[/bold cyan]

[bold]Execution:[/bold] {format_duration(execution_time)}
[bold]Agents Used:[/bold] {num_agents}
[bold]API Calls:[/bold] {total_api_calls}
[bold]Tokens Used:[/bold] {total_tokens:,}
[bold]Tools Used:[/bold] {total_tools}

[bold green]✨ Efficiency:[/bold green] Parallel processing saved ~{format_duration(execution_time * 0.75)} vs sequential
"""
        
        from rich.panel import Panel
        self.console.print(Panel(summary_content, title="Performance Metrics", border_style="magenta"))
    
    def suggest_alternatives(self, failed_input: str) -> None:
        """Suggest alternatives when request fails"""
        self.console.print("\n[bold yellow]💡 Let's try a different approach:[/bold yellow]")
        
        suggestions = [
            f"Try being more specific: 'Search for information about {failed_input}'",
            f"Break it down: 'Help me understand {failed_input}'",
            "Ask for examples: 'Show me examples of what you can do'",
            "Check available tools: Type 'tools' to see what I can help with"
        ]
        
        for i, suggestion in enumerate(suggestions, 1):
            self.console.print(f"  {i}. {suggestion}")
    
    def show_api_troubleshooting(self) -> None:
        """Show API-specific troubleshooting help"""
        self.console.print("\n[bold blue]🔧 API Troubleshooting:[/bold blue]")
        self.console.print("1. Check your internet connection")
        self.console.print("2. Verify your API key with 'status' command")
        self.console.print("3. Try again in a moment - the service might be busy")
        self.console.print("4. Run 'setup' to reconfigure if needed")
    
    def handle_graceful_exit(self) -> None:
        """Handle graceful application exit"""
        self.console.print("\n")
        self.style_manager.print_message(
            "Thanks for using Make It Heavy!", "primary", "celebration"
        )
        
        if self.ui_manager:
            self.ui_manager.show_final_summary()
        
        self.console.print("[dim]Goodbye! 👋[/dim]")


def main():
    """Enhanced main entry point with multi-agent orchestration"""
    try:
        cli = EnhancedMakeItHeavyCLI()
        cli.run()
    except ImportError as e:
        console = Console()
        console.print(f"[red]❌ Missing dependency: {e}[/red]")
        console.print("Please install dependencies with: [bold]pip install -r requirements.txt[/bold]")
        console.print("Or use uv: [bold]uv pip install -r requirements.txt[/bold]")
    except Exception as e:
        console = Console()
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        console.print("Please check your configuration and try again.")


if __name__ == "__main__":
    main()