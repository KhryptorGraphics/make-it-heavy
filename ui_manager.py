"""
Enhanced UI Manager for Make It Heavy
Provides rich terminal output, progress tracking, and real-time updates
"""
import time
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, MofNCompleteColumn
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.columns import Columns
from rich import box
from rich.status import Status

@dataclass
class AgentMetrics:
    """Metrics for individual agent performance"""
    agent_id: str
    status: str = "initializing"  # initializing, running, completed, failed
    current_task: str = "Starting..."
    iterations: int = 0
    max_iterations: int = 10
    tools_used: List[str] = None
    api_calls: int = 0
    tokens_used: int = 0
    start_time: float = 0
    end_time: float = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.tools_used is None:
            self.tools_used = []
        if self.errors is None:
            self.errors = []
        if self.start_time == 0:
            self.start_time = time.time()

@dataclass
class OrchestratorMetrics:
    """Metrics for orchestrator-level operations"""
    total_agents: int = 0
    completed_agents: int = 0
    failed_agents: int = 0
    questions_generated: List[str] = None
    synthesis_progress: float = 0.0
    start_time: float = 0
    phase: str = "initializing"  # initializing, generating_questions, running_agents, synthesizing, completed
    
    def __post_init__(self):
        if self.questions_generated is None:
            self.questions_generated = []
        if self.start_time == 0:
            self.start_time = time.time()

class UIManager:
    """Enhanced UI Manager with rich terminal output"""
    
    def __init__(self, silent: bool = False, verbose: bool = False):
        self.console = Console()
        self.silent = silent
        self.verbose = verbose
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.orchestrator_metrics = OrchestratorMetrics()
        self.timeline: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        
    def log_timeline(self, event: str, details: str = "", level: str = "INFO"):
        """Add event to timeline with timestamp"""
        with self.lock:
            self.timeline.append({
                "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "event": event,
                "details": details,
                "level": level
            })
    
    def create_agent_metrics(self, agent_id: str, max_iterations: int = 10) -> AgentMetrics:
        """Create metrics tracking for an agent"""
        metrics = AgentMetrics(agent_id=agent_id, max_iterations=max_iterations)
        self.agent_metrics[agent_id] = metrics
        self.log_timeline(f"Agent {agent_id} initialized", f"Max iterations: {max_iterations}")
        return metrics
    
    def update_agent_status(self, agent_id: str, status: str, current_task: str = ""):
        """Update agent status"""
        if agent_id in self.agent_metrics:
            with self.lock:
                self.agent_metrics[agent_id].status = status
                if current_task:
                    self.agent_metrics[agent_id].current_task = current_task
                self.log_timeline(f"Agent {agent_id} status", f"{status}: {current_task}")
    
    def update_agent_iteration(self, agent_id: str, iteration: int):
        """Update agent iteration count"""
        if agent_id in self.agent_metrics:
            with self.lock:
                self.agent_metrics[agent_id].iterations = iteration
    
    def log_tool_usage(self, agent_id: str, tool_name: str, success: bool = True):
        """Log tool usage for an agent"""
        if agent_id in self.agent_metrics:
            with self.lock:
                self.agent_metrics[agent_id].tools_used.append(tool_name)
                if success:
                    self.log_timeline(f"Agent {agent_id} tool", f"Used {tool_name} successfully")
                else:
                    self.log_timeline(f"Agent {agent_id} tool", f"Failed to use {tool_name}", "ERROR")
    
    def log_api_call(self, agent_id: str, tokens_used: int = 0):
        """Log API call with token usage"""
        if agent_id in self.agent_metrics:
            with self.lock:
                self.agent_metrics[agent_id].api_calls += 1
                self.agent_metrics[agent_id].tokens_used += tokens_used
    
    def log_error(self, agent_id: str, error_message: str):
        """Log error for an agent"""
        if agent_id in self.agent_metrics:
            with self.lock:
                self.agent_metrics[agent_id].errors.append(error_message)
                self.log_timeline(f"Agent {agent_id} error", error_message, "ERROR")
    
    def update_orchestrator_phase(self, phase: str, details: str = ""):
        """Update orchestrator phase"""
        with self.lock:
            self.orchestrator_metrics.phase = phase
            self.log_timeline(f"Orchestrator phase", f"{phase}: {details}")
    
    def set_questions_generated(self, questions: List[str]):
        """Set generated questions"""
        with self.lock:
            self.orchestrator_metrics.questions_generated = questions
            self.orchestrator_metrics.total_agents = len(questions)
            self.log_timeline("Questions generated", f"Generated {len(questions)} questions")
    
    def agent_completed(self, agent_id: str):
        """Mark agent as completed"""
        if agent_id in self.agent_metrics:
            with self.lock:
                self.agent_metrics[agent_id].status = "completed"
                self.agent_metrics[agent_id].end_time = time.time()
                self.orchestrator_metrics.completed_agents += 1
                self.log_timeline(f"Agent {agent_id} completed", f"Total completed: {self.orchestrator_metrics.completed_agents}")
    
    def agent_failed(self, agent_id: str, error: str):
        """Mark agent as failed"""
        if agent_id in self.agent_metrics:
            with self.lock:
                self.agent_metrics[agent_id].status = "failed"
                self.agent_metrics[agent_id].end_time = time.time()
                self.orchestrator_metrics.failed_agents += 1
                self.log_error(agent_id, error)
    
    def update_synthesis_progress(self, progress: float):
        """Update synthesis progress"""
        with self.lock:
            self.orchestrator_metrics.synthesis_progress = progress
    
    def create_agent_status_table(self) -> Table:
        """Create agent status table"""
        table = Table(title="Agent Status Dashboard", box=box.ROUNDED)
        table.add_column("Agent ID", style="cyan", width=10)
        table.add_column("Status", width=12)
        table.add_column("Current Task", style="dim", width=30)
        table.add_column("Progress", width=15)
        table.add_column("Tools Used", width=15)
        table.add_column("API Calls", width=10)
        table.add_column("Errors", width=8)
        
        for agent_id, metrics in self.agent_metrics.items():
            # Status with color coding
            status_color = {
                "initializing": "yellow",
                "running": "blue",
                "completed": "green",
                "failed": "red"
            }.get(metrics.status, "white")
            
            status_text = Text(metrics.status, style=status_color)
            
            # Progress bar
            progress_text = f"{metrics.iterations}/{metrics.max_iterations}"
            if metrics.status == "completed":
                progress_text = "✅ Done"
            elif metrics.status == "failed":
                progress_text = "❌ Failed"
            
            # Tools used
            tools_text = ", ".join(metrics.tools_used[-3:]) if metrics.tools_used else "None"
            if len(metrics.tools_used) > 3:
                tools_text += "..."
            
            # Error count
            error_count = len(metrics.errors)
            error_text = str(error_count) if error_count > 0 else "0"
            
            table.add_row(
                agent_id,
                status_text,
                metrics.current_task[:30] + "..." if len(metrics.current_task) > 30 else metrics.current_task,
                progress_text,
                tools_text,
                str(metrics.api_calls),
                error_text
            )
        
        return table
    
    def create_orchestrator_panel(self) -> Panel:
        """Create orchestrator status panel"""
        phase_icons = {
            "initializing": "🔄",
            "generating_questions": "❓",
            "running_agents": "🤖",
            "synthesizing": "🔄",
            "completed": "✅"
        }
        
        icon = phase_icons.get(self.orchestrator_metrics.phase, "📊")
        
        elapsed_time = time.time() - self.orchestrator_metrics.start_time
        
        content = f"""
{icon} Phase: {self.orchestrator_metrics.phase.title()}
⏱️  Elapsed: {elapsed_time:.1f}s
🤖 Total Agents: {self.orchestrator_metrics.total_agents}
✅ Completed: {self.orchestrator_metrics.completed_agents}
❌ Failed: {self.orchestrator_metrics.failed_agents}
"""
        
        if self.orchestrator_metrics.synthesis_progress > 0:
            content += f"🔄 Synthesis: {self.orchestrator_metrics.synthesis_progress:.1f}%"
        
        return Panel(content.strip(), title="Orchestrator Status", border_style="blue")
    
    def create_timeline_panel(self, max_events: int = 10) -> Panel:
        """Create timeline panel with recent events"""
        recent_events = self.timeline[-max_events:] if len(self.timeline) > max_events else self.timeline
        
        timeline_content = []
        for event in recent_events:
            level_colors = {
                "INFO": "white",
                "ERROR": "red",
                "SUCCESS": "green"
            }
            color = level_colors.get(event["level"], "white")
            
            timeline_content.append(
                f"[{color}]{event['timestamp']} {event['event']}: {event['details']}[/{color}]"
            )
        
        content = "\n".join(timeline_content) if timeline_content else "No events yet..."
        
        return Panel(content, title="Timeline", border_style="yellow")
    
    def show_single_agent_progress(self, agent_id: str, max_duration: float = 300.0):
        """Show progress for single agent mode with timeout"""
        if self.silent:
            return
            
        if agent_id not in self.agent_metrics:
            # Create empty metrics if they don't exist
            self.create_agent_metrics(agent_id)
            
        metrics = self.agent_metrics[agent_id]
        start_time = time.time()
        
        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=6),
            Layout(name="main", size=15),
            Layout(name="timeline", size=10)
        )
        
        # Update layout
        layout["header"].update(Panel("🚀 Make It Heavy - Single Agent Mode", style="bold blue"))
        layout["main"].update(self.create_agent_status_table())
        layout["timeline"].update(self.create_timeline_panel())
        
        try:
            with Live(layout, refresh_per_second=4) as live:
                while (metrics.status in ["initializing", "running"] and 
                       time.time() - start_time < max_duration):
                    layout["main"].update(self.create_agent_status_table())
                    layout["timeline"].update(self.create_timeline_panel())
                    time.sleep(0.25)
        except Exception as e:
            # Gracefully handle any display errors
            self.log_timeline("Dashboard error", f"Display error: {e}", "ERROR")
    
    def show_orchestrator_dashboard(self, max_duration: float = 600.0):
        """Show real-time orchestrator dashboard with timeout"""
        if self.silent:
            return
            
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="status", size=8),
            Layout(name="agents", size=15),
            Layout(name="timeline", size=10)
        )
        
        layout["header"].update(Panel("🚀 Make It Heavy - Grok Heavy Mode", style="bold blue"))
        
        start_time = time.time()
        
        try:
            with Live(layout, refresh_per_second=4) as live:
                while (self.orchestrator_metrics.phase not in ["completed", "failed"] and 
                       time.time() - start_time < max_duration):
                    layout["status"].update(self.create_orchestrator_panel())
                    layout["agents"].update(self.create_agent_status_table())
                    layout["timeline"].update(self.create_timeline_panel())
                    time.sleep(0.25)
        except Exception as e:
            # Gracefully handle any display errors
            self.log_timeline("Dashboard error", f"Display error: {e}", "ERROR")
    
    def print_success(self, message: str):
        """Print success message"""
        if not self.silent:
            self.console.print(f"✅ {message}", style="green")
    
    def print_error(self, message: str):
        """Print error message"""
        if not self.silent:
            self.console.print(f"❌ {message}", style="red")
    
    def print_info(self, message: str):
        """Print info message"""
        if not self.silent:
            self.console.print(f"ℹ️  {message}", style="blue")
    
    def print_warning(self, message: str):
        """Print warning message"""
        if not self.silent:
            self.console.print(f"⚠️  {message}", style="yellow")
    
    def show_simple_progress(self, agent_id: str, message: str = "Processing..."):
        """Show simple progress without blocking dashboard"""
        if self.silent:
            return
            
        with self.console.status(f"[bold green]{message}") as status:
            if agent_id in self.agent_metrics:
                metrics = self.agent_metrics[agent_id]
                while metrics.status in ["initializing", "running"]:
                    status.update(f"[bold green]{message} (Iteration {metrics.iterations})")
                    time.sleep(0.5)
    
    def show_final_summary(self):
        """Show final execution summary"""
        if self.silent:
            return
            
        total_time = time.time() - self.orchestrator_metrics.start_time
        
        summary_table = Table(title="Execution Summary", box=box.ROUNDED)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="white")
        
        summary_table.add_row("Total Execution Time", f"{total_time:.2f}s")
        summary_table.add_row("Total Agents", str(self.orchestrator_metrics.total_agents))
        summary_table.add_row("Completed Agents", str(self.orchestrator_metrics.completed_agents))
        summary_table.add_row("Failed Agents", str(self.orchestrator_metrics.failed_agents))
        
        # Calculate totals
        total_api_calls = sum(metrics.api_calls for metrics in self.agent_metrics.values())
        total_tokens = sum(metrics.tokens_used for metrics in self.agent_metrics.values())
        total_tools = sum(len(metrics.tools_used) for metrics in self.agent_metrics.values())
        
        summary_table.add_row("Total API Calls", str(total_api_calls))
        summary_table.add_row("Total Tokens Used", str(total_tokens))
        summary_table.add_row("Total Tools Used", str(total_tools))
        
        self.console.print("\n")
        self.console.print(summary_table)
        self.console.print("\n")