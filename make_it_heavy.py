import time
import threading
import sys
from orchestrator import TaskOrchestrator
from ui_manager import UIManager

class OrchestratorCLI:
    def __init__(self):
        # Initialize UI Manager
        self.ui_manager = UIManager()
        
        # Initialize orchestrator with UI manager
        self.orchestrator = TaskOrchestrator(ui_manager=self.ui_manager)
        self.start_time = None
        self.running = False
        
        # Extract model name for display
        model_full = self.orchestrator.config['openrouter']['model']
        # Extract model name (e.g., "google/gemini-2.5-flash-preview-05-20" -> "GEMINI-2.5-FLASH")
        if '/' in model_full:
            model_name = model_full.split('/')[-1]
        else:
            model_name = model_full
        
        # Clean up model name for display
        model_parts = model_name.split('-')
        # Take first 3 parts for cleaner display (e.g., gemini-2.5-flash)
        clean_name = '-'.join(model_parts[:3]) if len(model_parts) >= 3 else model_name
        self.model_display = clean_name.upper() + " HEAVY"
        
    def clear_screen(self):
        """Properly clear the entire screen"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def format_time(self, seconds):
        """Format seconds into readable time string"""
        if seconds < 60:
            return f"{int(seconds)}S"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}M{secs}S"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}H{minutes}M"
    
    def create_progress_bar(self, status):
        """Create progress visualization based on status"""
        # ANSI color codes
        ORANGE = '\033[38;5;208m'  # Orange color
        RED = '\033[91m'           # Red color
        RESET = '\033[0m'          # Reset color
        
        if status == "QUEUED":
            return "○ " + "·" * 70
        elif status == "INITIALIZING...":
            return f"{ORANGE}◐{RESET} " + "·" * 70
        elif status == "PROCESSING...":
            # Animated processing bar in orange
            dots = f"{ORANGE}:" * 10 + f"{RESET}" + "·" * 60
            return f"{ORANGE}●{RESET} " + dots
        elif status == "COMPLETED":
            return f"{ORANGE}●{RESET} " + f"{ORANGE}:" * 70 + f"{RESET}"
        elif status.startswith("FAILED"):
            return f"{RED}✗{RESET} " + f"{RED}×" * 70 + f"{RESET}"
        else:
            return f"{ORANGE}◐{RESET} " + "·" * 70
    
    def update_display(self):
        """Update the console display with current status"""
        if not self.running:
            return
            
        # Calculate elapsed time
        elapsed = time.time() - self.start_time if self.start_time else 0
        time_str = self.format_time(elapsed)
        
        # Get current progress
        progress = self.orchestrator.get_progress_status()
        
        # Clear screen properly
        self.clear_screen()
        
        # Header with dynamic model name
        print(self.model_display)
        if self.running:
            print(f"● RUNNING • {time_str}")
        else:
            print(f"● COMPLETED • {time_str}")
        print()
        
        # Agent status lines
        for i in range(self.orchestrator.num_agents):
            status = progress.get(i, "QUEUED")
            progress_bar = self.create_progress_bar(status)
            print(f"AGENT {i+1:02d}  {progress_bar}")
        
        print()
        sys.stdout.flush()
    
    def progress_monitor(self):
        """Monitor and update progress display in separate thread"""
        while self.running:
            self.update_display()
            time.sleep(1.0)  # Update every 1 second (reduced flicker)
    
    def run_task(self, user_input):
        """Run orchestrator task with rich UI dashboard"""
        self.start_time = time.time()
        self.running = True
        
        # Start rich dashboard in background thread
        dashboard_thread = threading.Thread(target=self.ui_manager.show_orchestrator_dashboard, daemon=True)
        dashboard_thread.start()
        
        try:
            # Run the orchestrator with UI integration
            result = self.orchestrator.orchestrate(user_input)
            
            # Stop monitoring
            self.running = False
            
            # Wait a moment for dashboard to update
            time.sleep(1.0)
            
            # Show final results with rich formatting
            self.ui_manager.console.print("\n" + "="*80)
            self.ui_manager.console.print("🎆 FINAL RESULTS", style="bold green")
            self.ui_manager.console.print("="*80)
            self.ui_manager.console.print()
            self.ui_manager.console.print(result)
            self.ui_manager.console.print()
            self.ui_manager.console.print("="*80)
            
            # Show execution summary
            self.ui_manager.show_final_summary()
            
            return result
            
        except Exception as e:
            self.running = False
            self.ui_manager.print_error(f"Error during orchestration: {str(e)}")
            return None
    
    def interactive_mode(self):
        """Run interactive CLI session with rich UI"""
        # Show startup banner with rich formatting
        self.ui_manager.print_info("🚀 Make It Heavy - Grok Heavy Mode")
        self.ui_manager.print_info(f"Configured for {self.orchestrator.num_agents} parallel agents")
        self.ui_manager.print_info("Type 'quit', 'exit', or 'bye' to exit")
        self.ui_manager.console.print("-" * 50)
        
        try:
            orchestrator_config = self.orchestrator.config['openrouter']
            self.ui_manager.print_success(f"Using model: {orchestrator_config['model']}")
            self.ui_manager.print_success("Orchestrator initialized successfully!")
            self.ui_manager.print_warning("Note: Make sure to set your OpenRouter API key in config.yaml")
            self.ui_manager.console.print("-" * 50)
        except Exception as e:
            self.ui_manager.print_error(f"Error initializing orchestrator: {e}")
            self.ui_manager.console.print("Make sure you have:")
            self.ui_manager.console.print("1. Set your OpenRouter API key in config.yaml")
            self.ui_manager.console.print("2. Installed all dependencies with: pip install -r requirements.txt")
            return
        
        while True:
            try:
                user_input = input("\n🤖 Enter your question for multi-agent analysis: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    self.ui_manager.print_success("Goodbye!")
                    break
                
                if not user_input:
                    self.ui_manager.print_warning("Please enter a question or command.")
                    continue
                
                self.ui_manager.print_info("\nOrchestrator: Starting multi-agent analysis...")
                self.ui_manager.console.print()
                
                # Run task with rich UI dashboard
                result = self.run_task(user_input)
                
                if result is None:
                    self.ui_manager.print_error("Task failed. Please try again.")
                
            except KeyboardInterrupt:
                self.ui_manager.print_warning("\n\nExiting...")
                break
            except Exception as e:
                self.ui_manager.print_error(f"Error: {e}")
                self.ui_manager.print_info("Please try again or type 'quit' to exit.")

def main():
    """Main entry point for the orchestrator CLI"""
    try:
        cli = OrchestratorCLI()
        cli.interactive_mode()
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        print("Or use uv: uv pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("Please check your configuration and try again.")

if __name__ == "__main__":
    main()