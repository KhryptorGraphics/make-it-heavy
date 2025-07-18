from agent import OpenRouterAgent
from ui_manager import UIManager
import threading
import time

def main():
    """Main entry point for the OpenRouter agent with enhanced UI"""
    # Initialize UI Manager
    ui_manager = UIManager()
    
    # Show startup banner
    ui_manager.print_info("🚀 Make It Heavy - Single Agent Mode")
    ui_manager.print_info("Type 'quit', 'exit', or 'bye' to exit")
    ui_manager.console.print("-" * 50)
    
    try:
        # Initialize agent with UI manager
        agent = OpenRouterAgent(ui_manager=ui_manager, agent_id="main_agent")
        ui_manager.print_success("Agent initialized successfully!")
        ui_manager.print_info(f"Using model: {agent.config['openrouter']['model']}")
        ui_manager.print_warning("Note: Make sure to set your OpenRouter API key in config.yaml")
        ui_manager.console.print("-" * 50)
    except Exception as e:
        ui_manager.print_error(f"Error initializing agent: {e}")
        ui_manager.console.print("Make sure you have:")
        ui_manager.console.print("1. Set your OpenRouter API key in config.yaml")
        ui_manager.console.print("2. Installed all dependencies with: pip install -r requirements.txt")
        return
    
    while True:
        try:
            user_input = input("\n🤖 Enter your question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                ui_manager.print_success("Goodbye!")
                ui_manager.show_final_summary()
                break
            
            if not user_input:
                ui_manager.print_warning("Please enter a question or command.")
                continue
            
            # Show progress in a non-blocking way
            progress_thread = threading.Thread(
                target=ui_manager.show_simple_progress, 
                args=("main_agent", "Agent is processing your request..."), 
                daemon=True
            )
            progress_thread.start()
            
            # Run agent with enhanced tracking
            response = agent.run(user_input)
            
            # Display response with formatting
            ui_manager.console.print("\n" + "="*60)
            ui_manager.console.print("🤖 Agent Response:", style="bold green")
            ui_manager.console.print("="*60)
            ui_manager.console.print(response)
            ui_manager.console.print("="*60 + "\n")
            
        except KeyboardInterrupt:
            ui_manager.print_warning("\n\nExiting...")
            ui_manager.show_final_summary()
            break
        except Exception as e:
            ui_manager.print_error(f"Error: {e}")
            ui_manager.print_info("Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        print("Or use uv: uv pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("Please check your configuration and try again.")