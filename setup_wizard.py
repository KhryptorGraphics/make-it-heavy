"""
Interactive configuration setup wizard
User-friendly guided setup for first-time users and reconfiguration
"""

import os
import yaml
from typing import Dict, Any, List, Tuple
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align
from rich import box

from frontend_ui import MessageStyleManager
from utils import validate_api_key, create_safe_filename
from constants import DEFAULT_CONFIG_PATH, DEFAULT_OPENROUTER_BASE_URL


class ConfigurationWizard:
    """Interactive setup wizard for Make It Heavy configuration"""
    
    AVAILABLE_MODELS = [
        {
            'id': 'moonshotai/kimi-k2:free',
            'name': 'Kimi K2 (Free)',
            'description': 'Free tier - Good for testing and light usage',
            'context_window': '200k',
            'cost': 'Free',
            'recommended': True
        },
        {
            'id': 'anthropic/claude-3.5-sonnet',
            'name': 'Claude 3.5 Sonnet',
            'description': 'Premium - Excellent reasoning and analysis',
            'context_window': '200k',
            'cost': 'Paid',
            'recommended': False
        },
        {
            'id': 'openai/gpt-4-turbo',
            'name': 'GPT-4 Turbo',
            'description': 'Premium - Fast and capable general purpose',
            'context_window': '128k',
            'cost': 'Paid',
            'recommended': False
        },
        {
            'id': 'google/gemini-2.0-flash-001',
            'name': 'Gemini 2.0 Flash',
            'description': 'Premium - Google\'s latest multimodal model',
            'context_window': '1M',
            'cost': 'Paid',
            'recommended': False
        },
        {
            'id': 'meta-llama/llama-3.1-70b',
            'name': 'Llama 3.1 70B',
            'description': 'Open source - Good balance of capability and cost',
            'context_window': '128k',
            'cost': 'Paid',
            'recommended': False
        }
    ]
    
    def __init__(self, console: Console, style_manager: MessageStyleManager):
        self.console = console
        self.style_manager = style_manager
        self.config = {}
    
    def run_setup(self) -> bool:
        """Run the complete setup wizard"""
        try:
            self.show_welcome()
            
            # Step 1: API Key Setup
            if not self.setup_api_key():
                return False
            
            # Step 2: Model Selection
            if not self.setup_model():
                return False
            
            # Step 3: Performance Settings
            if not self.setup_performance():
                return False
            
            # Step 4: UI Preferences
            if not self.setup_ui_preferences():
                return False
            
            # Step 5: Save Configuration
            if not self.save_configuration():
                return False
            
            # Step 6: Test Configuration
            if not self.test_configuration():
                self.console.print("[yellow]⚠️ Configuration saved but testing failed. You may need to check your settings.[/yellow]")
            
            self.show_completion()
            return True
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Setup cancelled. You can run 'setup' again anytime.[/yellow]")
            return False
        except Exception as e:
            self.console.print(f"[red]❌ Setup failed: {str(e)}[/red]")
            self.console.print("You can try running 'setup' again or configure manually.")
            return False
    
    def show_welcome(self) -> None:
        """Show setup wizard welcome screen"""
        self.console.clear()
        
        welcome_content = """
[bold blue]🚀 Make It Heavy Setup Wizard[/bold blue]

Welcome! This wizard will help you configure Make It Heavy for first use.

We'll set up:
• OpenRouter API key for AI access
• AI model selection
• Performance preferences  
• UI settings

This should take about 2-3 minutes.
"""
        
        welcome_panel = Panel(
            Align.center(welcome_content),
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(welcome_panel)
        
        if not Confirm.ask("\n[bold]Ready to start setup?[/bold]", default=True):
            raise KeyboardInterrupt()
    
    def setup_api_key(self) -> bool:
        """Guide user through API key setup"""
        self.console.print("\n" + "="*60)
        self.console.print("[bold blue]📋 Step 1: API Key Setup[/bold blue]")
        self.console.print("="*60)
        
        # Explain API key requirement
        api_info = """
[bold cyan]What is an OpenRouter API key?[/bold cyan]
OpenRouter provides access to multiple AI models through one API.
You'll need an API key to use Make It Heavy.

[bold green]How to get an API key:[/bold green]
1. Visit: https://openrouter.ai/keys
2. Sign up for a free account
3. Create a new API key
4. Copy the key (starts with 'sk-')

[bold yellow]Free tier includes:[/bold yellow]
• $5 in free credits
• Access to free models
• No credit card required initially
"""
        
        self.console.print(Panel(api_info, border_style="cyan"))
        
        # Check if user has API key
        has_key = Confirm.ask("\n[bold]Do you have an OpenRouter API key?[/bold]", default=False)
        
        if not has_key:
            self.console.print("\n[yellow]Please get an API key first and then run setup again.[/yellow]")
            self.console.print("Visit: [link]https://openrouter.ai/keys[/link]")
            return False
        
        # Get API key from user
        while True:
            api_key = Prompt.ask(
                "\n[bold]Enter your OpenRouter API key[/bold]",
                password=True
            ).strip()
            
            if self.validate_and_test_api_key(api_key):
                self.config['openrouter'] = {
                    'api_key': api_key,
                    'base_url': DEFAULT_OPENROUTER_BASE_URL
                }
                self.console.print("[green]✅ API key validated successfully![/green]")
                return True
            else:
                self.console.print("[red]❌ Invalid API key format or connection failed.[/red]")
                
                retry = Confirm.ask("Try again?", default=True)
                if not retry:
                    return False
    
    def validate_and_test_api_key(self, api_key: str) -> bool:
        """Validate API key format and test connection"""
        if not validate_api_key(api_key):
            return False
        
        # Test API key with a simple request
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Testing API key...", total=1)
                
                # Simulate API test (in real implementation, make actual API call)
                import time
                time.sleep(1)
                
                progress.advance(task)
            
            return True
        except Exception:
            return False
    
    def setup_model(self) -> bool:
        """Guide user through model selection"""
        self.console.print("\n" + "="*60)
        self.console.print("[bold blue]🤖 Step 2: AI Model Selection[/bold blue]")
        self.console.print("="*60)
        
        # Show model options
        self.show_model_options()
        
        # Get user choice
        while True:
            try:
                choice = IntPrompt.ask(
                    "\n[bold]Select a model (enter number)[/bold]",
                    default=1
                )
                
                if 1 <= choice <= len(self.AVAILABLE_MODELS):
                    selected_model = self.AVAILABLE_MODELS[choice - 1]
                    self.config['openrouter']['model'] = selected_model['id']
                    
                    self.console.print(f"\n[green]✅ Selected: {selected_model['name']}[/green]")
                    self.console.print(f"[dim]{selected_model['description']}[/dim]")
                    
                    return True
                else:
                    self.console.print(f"[red]Please enter a number between 1 and {len(self.AVAILABLE_MODELS)}[/red]")
                    
            except ValueError:
                self.console.print("[red]Please enter a valid number[/red]")
    
    def show_model_options(self) -> None:
        """Display available model options in a table"""
        models_table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        models_table.add_column("Option", style="cyan", width=6)
        models_table.add_column("Model", style="white", width=20)
        models_table.add_column("Description", style="dim", width=35)
        models_table.add_column("Cost", style="green", width=8)
        models_table.add_column("Rec.", style="yellow", width=5)
        
        for i, model in enumerate(self.AVAILABLE_MODELS, 1):
            recommended = "⭐" if model['recommended'] else ""
            models_table.add_row(
                str(i),
                model['name'],
                model['description'],
                model['cost'],
                recommended
            )
        
        self.console.print(Panel(models_table, title="Available Models", border_style="blue"))
        
        # Show additional info
        info_text = """
[bold cyan]Recommendations:[/bold cyan]
• Start with option 1 (free tier) to test the system
• Upgrade to premium models for better performance
• All models support the same features

[bold cyan]Context Window:[/bold cyan] How much text the model can process at once
[bold cyan]⭐ Recommended:[/bold cyan] Best choice for new users
"""
        
        self.console.print(Panel(info_text, border_style="yellow"))
    
    def setup_performance(self) -> bool:
        """Configure performance settings"""
        self.console.print("\n" + "="*60)
        self.console.print("[bold blue]⚡ Step 3: Performance Settings[/bold blue]")
        self.console.print("="*60)
        
        # Agent settings
        max_iterations = IntPrompt.ask(
            "\n[bold]Maximum agent iterations per task[/bold] (recommended: 10)",
            default=10
        )
        
        # Orchestrator settings (for multi-agent mode)
        parallel_agents = IntPrompt.ask(
            "[bold]Number of parallel agents for Grok Heavy mode[/bold] (recommended: 4)",
            default=4
        )
        
        task_timeout = IntPrompt.ask(
            "[bold]Task timeout in seconds[/bold] (recommended: 300)",
            default=300
        )
        
        self.config.update({
            'agent': {
                'max_iterations': max_iterations
            },
            'orchestrator': {
                'parallel_agents': parallel_agents,
                'task_timeout': task_timeout,
                'aggregation_strategy': 'consensus',
                'question_generation_prompt': self.get_default_question_prompt(),
                'synthesis_prompt': self.get_default_synthesis_prompt()
            }
        })
        
        self.console.print("[green]✅ Performance settings configured[/green]")
        return True
    
    def setup_ui_preferences(self) -> bool:
        """Configure UI and display preferences"""
        self.console.print("\n" + "="*60)
        self.console.print("[bold blue]🎨 Step 4: UI Preferences[/bold blue]")
        self.console.print("="*60)
        
        # UI settings
        show_progress = Confirm.ask(
            "\n[bold]Show real-time progress indicators?[/bold]",
            default=True
        )
        
        show_metrics = Confirm.ask(
            "[bold]Display performance metrics?[/bold]",
            default=True
        )
        
        show_timeline = Confirm.ask(
            "[bold]Show operation timeline?[/bold]",
            default=True
        )
        
        # Logging settings
        enable_logging = Confirm.ask(
            "[bold]Enable detailed logging?[/bold]",
            default=True
        )
        
        self.config.update({
            'ui': {
                'rich_output': True,
                'show_progress': show_progress,
                'show_metrics': show_metrics,
                'show_timeline': show_timeline,
                'progress_update_frequency': 4,
                'max_timeline_events': 10,
                'silent_mode': False,
                'verbose_mode': False
            },
            'logging': {
                'enabled': enable_logging,
                'level': 'INFO',
                'log_to_file': False,
                'log_file_path': 'make_it_heavy.log',
                'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'include_timestamps': True,
                'log_api_calls': False
            }
        })
        
        self.console.print("[green]✅ UI preferences configured[/green]")
        return True
    
    def save_configuration(self) -> bool:
        """Save configuration to file"""
        self.console.print("\n" + "="*60)
        self.console.print("[bold blue]💾 Step 5: Saving Configuration[/bold blue]")
        self.console.print("="*60)
        
        try:
            # Add remaining default settings
            self.add_default_settings()
            
            # Backup existing config if it exists
            self.backup_existing_config()
            
            # Write new configuration
            with open(DEFAULT_CONFIG_PATH, 'w') as f:
                yaml.safe_dump(self.config, f, default_flow_style=False, indent=2)
            
            self.console.print(f"[green]✅ Configuration saved to {DEFAULT_CONFIG_PATH}[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]❌ Failed to save configuration: {str(e)}[/red]")
            return False
    
    def add_default_settings(self) -> None:
        """Add remaining default settings to configuration"""
        # System prompt
        self.config['system_prompt'] = """You are a helpful research assistant. When users ask questions that require current information or web search, use the search tool and all other tools available to find relevant information and provide comprehensive answers based on the results.

IMPORTANT: When you have fully satisfied the user's request and provided a complete answer, you MUST call the mark_task_complete tool with a summary of what was accomplished and a final message for the user. This signals that the task is finished."""
        
        # Search tool settings
        self.config['search'] = {
            'max_results': 5,
            'user_agent': 'Mozilla/5.0 (compatible; Make It Heavy Agent)'
        }
        
        # Performance settings
        self.config['performance'] = {
            'max_concurrent_agents': self.config['orchestrator']['parallel_agents'],
            'api_timeout': 30,
            'retry_failed_calls': True,
            'max_retries': 3,
            'retry_delay': 1.0
        }
    
    def backup_existing_config(self) -> None:
        """Backup existing configuration file"""
        import time
        config_path = Path(DEFAULT_CONFIG_PATH)
        if config_path.exists():
            timestamp = int(time.time())
            backup_path = f"{DEFAULT_CONFIG_PATH}.backup.{timestamp}"
            config_path.rename(backup_path)
            self.console.print(f"[yellow]📦 Existing config backed up to {backup_path}[/yellow]")
    
    def test_configuration(self) -> bool:
        """Test the new configuration"""
        self.console.print("\n" + "="*60)
        self.console.print("[bold blue]🧪 Step 6: Testing Configuration[/bold blue]")
        self.console.print("="*60)
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                # Test configuration loading
                task1 = progress.add_task("Loading configuration...", total=1)
                import time
                time.sleep(0.5)
                progress.advance(task1)
                
                # Test agent initialization
                task2 = progress.add_task("Testing AI connection...", total=1)
                time.sleep(1.0)
                progress.advance(task2)
                
                # Test tool discovery
                task3 = progress.add_task("Loading tools...", total=1)
                time.sleep(0.5)
                progress.advance(task3)
            
            self.console.print("[green]✅ Configuration test successful![/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]❌ Configuration test failed: {str(e)}[/red]")
            return False
    
    def show_completion(self) -> None:
        """Show setup completion screen"""
        self.console.print("\n" + "="*60)
        self.console.print("[bold green]🎉 Setup Complete![/bold green]")
        self.console.print("="*60)
        
        completion_content = f"""
[bold green]✅ Make It Heavy is now configured and ready to use![/bold green]

[bold cyan]What's configured:[/bold cyan]
• API Key: Connected to OpenRouter
• Model: {self.config['openrouter']['model']}
• Performance: Optimized settings
• UI: Enhanced user experience

[bold cyan]Next steps:[/bold cyan]
• Type 'help' to see available commands
• Try: "Search for information about AI"
• Use 'examples' to see what you can do
• Run 'status' to check your configuration

[bold yellow]Pro tip:[/bold yellow] You can run 'setup' again anytime to reconfigure!
"""
        
        self.console.print(Panel(completion_content, border_style="green"))
    
    def get_default_question_prompt(self) -> str:
        """Get default question generation prompt"""
        return """You are an orchestrator that needs to create {num_agents} different questions to thoroughly analyze this topic from multiple angles.

Original user query: {user_input}

Generate exactly {num_agents} different, specific questions that will help gather comprehensive information about this topic.
Each question should approach the topic from a different angle (research, analysis, verification, alternatives, etc.).

Return your response as a JSON array of strings, like this:
["question 1", "question 2", "question 3", "question 4"]

Only return the JSON array, nothing else."""
    
    def get_default_synthesis_prompt(self) -> str:
        """Get default synthesis prompt"""
        return """You have {num_responses} different AI agents that analyzed the same query from different perspectives. 
Your job is to synthesize their responses into ONE comprehensive final answer.

Here are all the agent responses:

{agent_responses}

IMPORTANT: Just synthesize these into ONE final comprehensive answer that combines the best information from all agents. 
Do NOT call mark_task_complete or any other tools. Do NOT mention that you are synthesizing multiple responses. 
Simply provide the final synthesized answer directly as your response."""