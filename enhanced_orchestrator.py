"""
Enhanced multi-agent orchestrator CLI with superior user experience
Frontend-focused improvements for Grok Heavy mode
"""

import sys
import threading
import time
from typing import Optional, Dict, Any

from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel

from orchestrator import TaskOrchestrator
from ui_manager import UIManager
from frontend_ui import (
    MessageStyleManager, UserFriendlyErrorHandler,
    InteractiveInputManager, HelpSystem, WelcomeScreen
)
from exceptions import OrchestrationError, APIError, ConfigurationError
from constants import EXIT_COMMANDS
from utils import load_config, validate_api_key, format_duration


class EnhancedOrchestratorCLI:
    """Enhanced multi-agent orchestrator CLI with superior UX"""
    
    def __init__(self):
        self.console = Console()
        self.style_manager = MessageStyleManager(self.console)
        self.error_handler = UserFriendlyErrorHandler(self.console, self.style_manager)
        self.input_manager = InteractiveInputManager(self.console, self.style_manager)
        self.help_system = HelpSystem(self.console, self.style_manager)
        self.welcome_screen = WelcomeScreen(self.console, self.style_manager)
        
        self.ui_manager: Optional[UIManager] = None
        self.orchestrator: Optional[TaskOrchestrator] = None
        self.config: Optional[Dict[str, Any]] = None
        self.start_time: float = 0
        self.running: bool = False
    
    def run(self) -> None:
        """Main entry point with enhanced user experience"""
        try:
            # Show welcome screen
            self.welcome_screen.show_welcome("multi")
            
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
        """Initialize UI manager and orchestrator with error handling"""
        try:
            # Initialize UI Manager
            self.ui_manager = UIManager()
            self.style_manager.print_message(
                "Initializing Grok Heavy orchestrator...", "info", "working"
            )
            
            # Initialize orchestrator
            self.orchestrator = TaskOrchestrator(ui_manager=self.ui_manager)
            
            self.style_manager.print_message(
                "Grok Heavy orchestrator ready!", "success", "success"
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
        timeout = self.config.get('orchestrator', {}).get('task_timeout', 300)
        
        info_content = f"""
[bold green]✅ Grok Heavy Orchestrator Ready![/bold green]

[bold cyan]Configuration:[/bold cyan]
• Model: {model}
• Parallel Agents: {num_agents}
• Task Timeout: {timeout}s
• Strategy: Consensus synthesis

[bold cyan]How it works:[/bold cyan]
1. 🎯 AI generates specialized research questions
2. 🤖 {num_agents} agents work in parallel on different aspects
3. ⚡ Real-time progress tracking
4. 🔄 Intelligent synthesis of all results

[dim]Type 'help' for commands or ask a complex question![/dim]
"""
        
        self.console.print(self.style_manager.create_status_panel(
            "🚀 Grok Heavy Status", info_content, "green"
        ))
    
    def main_loop(self) -> None:
        """Enhanced main interaction loop"""
        self.style_manager.print_message(
            "Ready for multi-agent analysis! What would you like to explore?", 
            "primary", "rocket"
        )
        
        self.show_grok_heavy_tips()
        
        while True:
            try:
                # Get user input with enhanced interface
                user_input = self.input_manager.get_user_input(
                    "ask a complex question for multi-agent analysis"
                )
                
                # Handle special commands
                if self.handle_special_commands(user_input):
                    continue
                
                # Check for exit commands
                if user_input.lower() in EXIT_COMMANDS:
                    self.handle_graceful_exit()
                    break
                
                # Process user request with multi-agent orchestration
                self.process_user_request(user_input)
                
            except KeyboardInterrupt:
                self.handle_graceful_exit()
                break
            except Exception as e:
                self.error_handler.handle_error(e)
                self.style_manager.print_message(
                    "The orchestrator is still ready! Try again or type 'help'.", 
                    "info", "info"
                )
    
    def show_grok_heavy_tips(self) -> None:
        """Show tips for using Grok Heavy mode effectively"""
        tips_content = """
[bold cyan]💡 Grok Heavy Tips:[/bold cyan]
• Ask complex, multi-faceted questions for best results
• Try: "Analyze the impact of AI on education from multiple perspectives"
• Be specific about what you want to explore
• The more complex the topic, the better the parallel analysis

[bold cyan]Perfect for:[/bold cyan]
• Research topics with multiple angles
• Controversial subjects needing balanced views  
• Complex analysis requiring different perspectives
• Comprehensive reports and summaries
"""
        
        self.console.print(Panel(tips_content, title="🎯 Getting the Most from Grok Heavy", border_style="yellow"))
    
    def handle_special_commands(self, user_input: str) -> bool:
        """Handle special commands that don't require orchestration"""
        command = user_input.lower().strip()
        
        if command == 'help':
            self.help_system.show_main_help()
            self.show_orchestrator_specific_help()
            return True
        
        elif command == 'tools':
            self.help_system.show_tool_help()
            return True
        
        elif command == 'examples':
            self.show_orchestrator_examples()
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
            if topic == 'orchestrator':
                self.show_orchestrator_specific_help()
            else:
                self.help_system.show_specific_tool_help(topic)
            return True
        
        return False
    
    def show_orchestrator_specific_help(self) -> None:
        """Show help specific to orchestrator mode"""
        help_content = """
[bold cyan]🚀 Grok Heavy Mode Help[/bold cyan]

[bold]How it works:[/bold]
1. You ask a complex question
2. AI generates 4 specialized research questions
3. 4 agents work in parallel on different aspects
4. All results are synthesized into one comprehensive answer

[bold]Best practices:[/bold]
• Ask open-ended, complex questions
• Include multiple aspects you want explored
• Be specific about the context or domain
• Allow time for thorough analysis (can take 1-3 minutes)

[bold]Example questions:[/bold]
• "Analyze the pros and cons of remote work from economic, social, and productivity perspectives"
• "What are the implications of quantum computing for cybersecurity, industry, and research?"
• "Examine the environmental, economic, and social impacts of electric vehicles"

[bold]Performance:[/bold]
• Uses more API credits than single agent mode
• Takes longer but provides deeper analysis
• Best for research, analysis, and complex topics
"""
        
        self.console.print(Panel(help_content, title="Grok Heavy Mode Guide", border_style="blue"))
    
    def show_orchestrator_examples(self) -> None:
        """Show examples specifically for orchestrator mode"""
        examples = {
            "🔬 Research & Analysis": [
                "Analyze the impact of artificial intelligence on job markets from multiple perspectives",
                "Examine the benefits and risks of gene editing technology across different domains",
                "Research the causes and solutions for climate change from scientific, economic, and political angles"
            ],
            "📊 Comparative Analysis": [
                "Compare renewable energy sources in terms of efficiency, cost, and environmental impact",
                "Analyze different economic systems and their effects on society and innovation",
                "Examine various approaches to education reform and their potential outcomes"
            ],
            "🌐 Complex Topics": [
                "What are the implications of cryptocurrency adoption for finance, regulation, and society?",
                "How might space exploration impact technology, economics, and human development?",
                "Analyze the relationship between social media and mental health from multiple research perspectives"
            ],
            "💼 Business & Strategy": [
                "Evaluate the pros and cons of remote work from employer, employee, and economic perspectives",
                "Analyze the risks and opportunities of AI adoption in healthcare across different stakeholders",
                "Examine the impact of e-commerce on traditional retail, employment, and urban planning"
            ]
        }
        
        for category, example_list in examples.items():
            self.console.print(f"\n[bold]{category}[/bold]")
            for example in example_list:
                self.console.print(f"  • {example}")
        
        self.console.print(f"\n[bold cyan]💡 Tip:[/bold cyan] The more complex and multi-faceted your question, the better Grok Heavy performs!")
    
    def show_status(self) -> None:
        """Show current orchestrator status"""
        model = self.config.get('openrouter', {}).get('model', 'Unknown')
        api_key = self.config.get('openrouter', {}).get('api_key', '')
        num_agents = self.config.get('orchestrator', {}).get('parallel_agents', 4)
        timeout = self.config.get('orchestrator', {}).get('task_timeout', 300)
        
        # Mask API key for security
        masked_key = api_key[:8] + "*" * (len(api_key) - 12) + api_key[-4:] if len(api_key) > 12 else "Not configured"
        
        status_content = f"""
[bold cyan]🚀 Orchestrator Configuration[/bold cyan]

[bold]Model:[/bold] {model}
[bold]API Key:[/bold] {masked_key}
[bold]Parallel Agents:[/bold] {num_agents}
[bold]Task Timeout:[/bold] {timeout}s
[bold]Aggregation Strategy:[/bold] Consensus
[bold]Status:[/bold] Ready for multi-agent analysis

[bold cyan]📊 Performance Settings[/bold cyan]
• Max concurrent agents: {num_agents}
• API timeout: {self.config.get('performance', {}).get('api_timeout', 30)}s
• Retry failed calls: {self.config.get('performance', {}).get('retry_failed_calls', True)}
• Max retries: {self.config.get('performance', {}).get('max_retries', 3)}
"""
        
        self.console.print(self.style_manager.create_status_panel(
            "Grok Heavy Status", status_content, "blue"
        ))
    
    def process_user_request(self, user_input: str) -> None:
        """Process user request with multi-agent orchestration"""
        try:
            # Show orchestration start
            self.style_manager.print_message(
                "Starting Grok Heavy analysis...", "info", "magic"
            )
            
            self.show_orchestration_preview(user_input)
            
            # Start orchestration with enhanced tracking
            self.start_time = time.time()
            self.running = True
            
            # Start dashboard in background
            dashboard_thread = threading.Thread(
                target=self.ui_manager.show_orchestrator_dashboard,
                daemon=True
            )
            dashboard_thread.start()
            
            # Run orchestration
            result = self.orchestrator.orchestrate(user_input)
            
            # Stop tracking
            self.running = False
            execution_time = time.time() - self.start_time
            
            # Show results with enhanced formatting
            self.show_orchestration_results(result, execution_time)
            
            # Show completion celebration
            self.style_manager.print_message(
                "Grok Heavy analysis completed!", "success", "celebration"
            )
            
        except OrchestrationError as e:
            self.error_handler.handle_error(e)
            self.suggest_orchestration_alternatives(user_input)
        except APIError as e:
            self.error_handler.handle_error(e)
            self.show_api_troubleshooting()
        except Exception as e:
            self.error_handler.handle_error(e, show_technical=True)
    
    def show_orchestration_preview(self, user_input: str) -> None:
        """Show what the orchestration will do"""
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
        
        self.console.print(Panel(preview_content, title="🚀 Grok Heavy Preview", border_style="cyan"))
    
    def show_orchestration_results(self, result: str, execution_time: float) -> None:
        """Display orchestration results with enhanced formatting"""
        # Create results panel
        results_header = f"🎉 Grok Heavy Results ({format_duration(execution_time)})"
        
        results_panel = self.style_manager.create_status_panel(
            results_header, result, "green"
        )
        
        self.console.print("\n")
        self.console.print(results_panel)
        self.console.print("\n")
        
        # Show performance summary
        self.show_performance_summary(execution_time)
    
    def show_performance_summary(self, execution_time: float) -> None:
        """Show performance summary of the orchestration"""
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
        
        self.console.print(Panel(summary_content, title="Performance Metrics", border_style="magenta"))
    
    def suggest_orchestration_alternatives(self, failed_input: str) -> None:
        """Suggest alternatives when orchestration fails"""
        self.console.print("\n[bold yellow]💡 Let's try a different approach:[/bold yellow]")
        
        suggestions = [
            f"Try making the question more specific: 'Analyze {failed_input} from economic and social perspectives'",
            f"Break it into parts: 'What are the benefits and drawbacks of {failed_input}?'",
            "Use single agent mode for simpler questions",
            "Check that your question has multiple aspects to analyze"
        ]
        
        for i, suggestion in enumerate(suggestions, 1):
            self.console.print(f"  {i}. {suggestion}")
        
        # Offer to switch to single agent mode
        single_mode = Confirm.ask("\n[bold]Would you like to try this question in single agent mode?[/bold]", default=False)
        if single_mode:
            self.console.print("[cyan]💡 Tip: Use 'python main.py' for single agent mode[/cyan]")
    
    def show_api_troubleshooting(self) -> None:
        """Show API-specific troubleshooting help"""
        self.console.print("\n[bold blue]🔧 API Troubleshooting:[/bold blue]")
        self.console.print("1. Check your internet connection")
        self.console.print("2. Verify your API key has sufficient credits")
        self.console.print("3. Try a simpler question first")
        self.console.print("4. Check OpenRouter service status")
        self.console.print("5. Run 'setup' to reconfigure if needed")
    
    def handle_graceful_exit(self) -> None:
        """Handle graceful application exit"""
        self.running = False
        
        self.console.print("\n")
        self.style_manager.print_message(
            "Thanks for using Grok Heavy mode!", "primary", "celebration"
        )
        
        if self.ui_manager:
            self.ui_manager.show_final_summary()
        
        self.console.print("[dim]Goodbye! 👋[/dim]")


def main():
    """Enhanced main entry point for Grok Heavy mode"""
    try:
        cli = EnhancedOrchestratorCLI()
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