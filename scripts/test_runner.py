#!/usr/bin/env python3
"""
Advanced test runner script with parallel execution, watch mode, and mutation testing.
Provides comprehensive testing capabilities for the Make It Heavy project.
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path
from typing import List, Optional
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class TestRunner:
    """Advanced test runner with multiple execution modes."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {}
        
    def run_command(self, cmd: List[str], description: str = "") -> int:
        """Run a command and return exit code."""
        if description:
            print(f"\n🔬 {description}")
            print("=" * 50)
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=self.project_root)
        
        self.test_results[description or ' '.join(cmd)] = result.returncode
        return result.returncode
    
    def run_unit_tests(self, parallel: bool = False) -> int:
        """Run unit tests."""
        cmd = ["pytest", "tests/unit/", "-v"]
        if parallel:
            cmd.extend(["-n", "auto"])
        
        return self.run_command(cmd, "Unit Tests")
    
    def run_integration_tests(self, parallel: bool = False) -> int:
        """Run integration tests."""
        cmd = ["pytest", "tests/integration/", "-v"]
        if parallel:
            cmd.extend(["-n", "auto"])
            
        return self.run_command(cmd, "Integration Tests")
    
    def run_e2e_tests(self) -> int:
        """Run end-to-end tests."""
        cmd = ["pytest", "tests/e2e/", "-v", "--tb=short"]
        return self.run_command(cmd, "End-to-End Tests")
    
    def run_coverage_tests(self) -> int:
        """Run tests with coverage analysis."""
        cmd = [
            "pytest", 
            "--cov=.",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "--cov-fail-under=80"
        ]
        
        result = self.run_command(cmd, "Coverage Analysis")
        
        if result == 0:
            print("\n📊 Coverage report generated:")
            print(f"  HTML: {self.project_root}/htmlcov/index.html")
            print(f"  XML:  {self.project_root}/coverage.xml")
        
        return result
    
    def run_parallel_tests(self, test_type: str = "all") -> int:
        """Run tests in parallel."""
        if test_type == "unit":
            return self.run_unit_tests(parallel=True)
        elif test_type == "integration":
            return self.run_integration_tests(parallel=True)
        elif test_type == "fast":
            cmd = ["pytest", "-n", "auto", "-m", "not slow", "-v"]
            return self.run_command(cmd, "Fast Tests (Parallel)")
        else:
            cmd = ["pytest", "-n", "auto", "-v"]
            return self.run_command(cmd, "All Tests (Parallel)")
    
    def run_mutation_tests(self) -> int:
        """Run mutation testing."""
        print("\n🧬 Mutation Testing")
        print("=" * 50)
        
        # Check if mutmut is installed
        try:
            subprocess.run(["mutmut", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ mutmut not installed. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "mutmut"], check=True)
        
        # Run mutation testing on core modules
        core_modules = ["agent.py", "orchestrator.py", "utils.py", "exceptions.py"]
        
        for module in core_modules:
            if (self.project_root / module).exists():
                cmd = ["mutmut", "run", "--paths-to-mutate", module, "--CI"]
                result = self.run_command(cmd, f"Mutation Testing: {module}")
                
                if result == 0:
                    # Show results
                    subprocess.run(["mutmut", "results"], cwd=self.project_root)
        
        return 0
    
    def run_smoke_tests(self) -> int:
        """Run smoke tests for quick validation."""
        cmd = ["pytest", "-m", "smoke", "-v", "--tb=short"]
        return self.run_command(cmd, "Smoke Tests")
    
    def run_quality_checks(self) -> int:
        """Run code quality checks."""
        checks = [
            (["python", "-m", "py_compile"] + list(self.project_root.glob("*.py")), "Syntax Check"),
            (["pytest", "--collect-only", "-q"], "Test Collection"),
        ]
        
        total_result = 0
        for cmd, description in checks:
            result = self.run_command([str(c) for c in cmd], description)
            total_result += result
        
        return total_result
    
    def print_summary(self):
        """Print test execution summary."""
        print("\n" + "=" * 60)
        print("🧪 TEST EXECUTION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result == 0)
        failed_tests = total_tests - passed_tests
        
        print(f"\nTotal test suites: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        
        if failed_tests > 0:
            print("\n🔍 Failed test suites:")
            for description, result in self.test_results.items():
                if result != 0:
                    print(f"  ❌ {description}")
        
        print("\n📁 Generated artifacts:")
        artifacts = [
            ("htmlcov/index.html", "HTML Coverage Report"),
            ("coverage.xml", "XML Coverage Report"),
            (".coverage", "Coverage Database"),
        ]
        
        for artifact, description in artifacts:
            artifact_path = self.project_root / artifact
            if artifact_path.exists():
                print(f"  📄 {description}: {artifact_path}")


class TestWatcher(FileSystemEventHandler):
    """File system watcher for continuous testing."""
    
    def __init__(self, test_runner: TestRunner, test_command: List[str]):
        self.test_runner = test_runner
        self.test_command = test_command
        self.last_run = 0
        self.debounce_seconds = 2
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        # Only trigger on Python files
        if not event.src_path.endswith('.py'):
            return
        
        # Debounce rapid file changes
        now = time.time()
        if now - self.last_run < self.debounce_seconds:
            return
        
        self.last_run = now
        
        print(f"\n🔄 File changed: {event.src_path}")
        print("Running tests...")
        
        self.test_runner.run_command(self.test_command, "Auto-triggered Tests")


def run_watch_mode(test_runner: TestRunner, watch_type: str = "fast"):
    """Run tests in watch mode."""
    print("👀 Starting watch mode - tests will run automatically when files change")
    print("Press Ctrl+C to exit\n")
    
    # Determine test command based on watch type
    if watch_type == "unit":
        test_command = ["pytest", "tests/unit/", "--tb=short"]
    elif watch_type == "integration":
        test_command = ["pytest", "tests/integration/", "--tb=short"]
    elif watch_type == "fast":
        test_command = ["pytest", "-m", "not slow", "--tb=short"]
    else:
        test_command = ["pytest", "--tb=short"]
    
    # Set up file watcher
    event_handler = TestWatcher(test_runner, test_command)
    observer = Observer()
    observer.schedule(event_handler, test_runner.project_root, recursive=True)
    
    # Start watching
    observer.start()
    
    try:
        # Run tests initially
        test_runner.run_command(test_command, "Initial Test Run")
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping watch mode...")
        observer.stop()
    
    observer.join()


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Advanced test runner for Make It Heavy")
    
    # Test type arguments
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--coverage", action="store_true", help="Run coverage analysis")
    parser.add_argument("--smoke", action="store_true", help="Run smoke tests")
    parser.add_argument("--mutation", action="store_true", help="Run mutation testing")
    parser.add_argument("--quality", action="store_true", help="Run quality checks")
    
    # Execution mode arguments
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--watch", action="store_true", help="Run in watch mode")
    parser.add_argument("--watch-type", choices=["unit", "integration", "fast", "all"], 
                       default="fast", help="Type of tests to watch")
    
    # Special modes
    parser.add_argument("--all", action="store_true", help="Run all test types")
    parser.add_argument("--fast", action="store_true", help="Run fast tests only")
    parser.add_argument("--ci", action="store_true", help="Run CI-friendly test suite")
    
    args = parser.parse_args()
    
    # Create test runner
    runner = TestRunner()
    
    # Handle watch mode
    if args.watch:
        run_watch_mode(runner, args.watch_type)
        return
    
    # Determine which tests to run
    exit_code = 0
    
    if args.all or (not any([args.unit, args.integration, args.e2e, args.coverage, 
                            args.smoke, args.mutation, args.quality, args.fast, args.ci])):
        # Run all tests
        exit_code += runner.run_unit_tests(args.parallel)
        exit_code += runner.run_integration_tests(args.parallel)
        exit_code += runner.run_e2e_tests()
        exit_code += runner.run_coverage_tests()
    
    if args.unit:
        exit_code += runner.run_unit_tests(args.parallel)
    
    if args.integration:
        exit_code += runner.run_integration_tests(args.parallel)
    
    if args.e2e:
        exit_code += runner.run_e2e_tests()
    
    if args.coverage:
        exit_code += runner.run_coverage_tests()
    
    if args.smoke:
        exit_code += runner.run_smoke_tests()
    
    if args.mutation:
        exit_code += runner.run_mutation_tests()
    
    if args.quality:
        exit_code += runner.run_quality_checks()
    
    if args.fast:
        exit_code += runner.run_parallel_tests("fast")
    
    if args.parallel and not any([args.unit, args.integration]):
        exit_code += runner.run_parallel_tests()
    
    if args.ci:
        # CI-friendly test suite
        exit_code += runner.run_unit_tests(parallel=True)
        exit_code += runner.run_integration_tests(parallel=True)
        exit_code += runner.run_coverage_tests()
    
    # Print summary
    runner.print_summary()
    
    # Exit with appropriate code
    sys.exit(min(exit_code, 1))  # Cap at 1 for shell compatibility


if __name__ == "__main__":
    main()