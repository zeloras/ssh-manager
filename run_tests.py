#!/usr/bin/env python3
"""
Comprehensive Test Runner for SSH Profile Manager

This script provides a unified interface for running all tests,
generating reports, and validating the codebase before commits or releases.

Usage:
    python run_tests.py [options]

Examples:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --coverage         # Run tests with coverage
    python run_tests.py --performance      # Run performance tests
    python run_tests.py --report           # Generate comprehensive report
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    @classmethod
    def disable(cls):
        """Disable colors for non-terminal output."""
        cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = ''
        cls.MAGENTA = cls.CYAN = cls.WHITE = cls.BOLD = ''
        cls.UNDERLINE = cls.END = ''


class TestResult:
    """Represents the result of a test execution."""

    def __init__(self, name: str, success: bool, duration: float,
                 output: str = "", error: str = ""):
        self.name = name
        self.success = success
        self.duration = duration
        self.output = output
        self.error = error
        self.timestamp = datetime.now()


class TestRunner:
    """Comprehensive test runner for SSH Profile Manager."""

    def __init__(self, verbose: bool = False, no_color: bool = False):
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.start_time = time.time()

        if no_color or not sys.stdout.isatty():
            Colors.disable()

    def log(self, message: str, color: str = Colors.WHITE):
        """Log a message with optional color."""
        print(f"{color}{message}{Colors.END}")

    def log_success(self, message: str):
        """Log a success message."""
        self.log(f"✅ {message}", Colors.GREEN)

    def log_error(self, message: str):
        """Log an error message."""
        self.log(f"❌ {message}", Colors.RED)

    def log_warning(self, message: str):
        """Log a warning message."""
        self.log(f"⚠️  {message}", Colors.YELLOW)

    def log_info(self, message: str):
        """Log an info message."""
        self.log(f"ℹ️  {message}", Colors.BLUE)

    def log_section(self, title: str):
        """Log a section header."""
        separator = "=" * 60
        self.log(f"\n{separator}", Colors.CYAN)
        self.log(f"{title.center(60)}", Colors.CYAN + Colors.BOLD)
        self.log(f"{separator}\n", Colors.CYAN)

    def run_command(self, command: List[str], name: str,
                   cwd: Optional[str] = None) -> TestResult:
        """Run a command and return the result."""
        self.log_info(f"Running {name}...")

        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=300  # 5 minute timeout
            )

            duration = time.time() - start_time
            success = result.returncode == 0

            if success:
                self.log_success(f"{name} completed in {duration:.2f}s")
            else:
                self.log_error(f"{name} failed in {duration:.2f}s")
                if self.verbose or not success:
                    print(f"STDOUT:\n{result.stdout}")
                    print(f"STDERR:\n{result.stderr}")

            test_result = TestResult(
                name=name,
                success=success,
                duration=duration,
                output=result.stdout,
                error=result.stderr
            )

            self.results.append(test_result)
            return test_result

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.log_error(f"{name} timed out after {duration:.2f}s")

            test_result = TestResult(
                name=name,
                success=False,
                duration=duration,
                error="Command timed out"
            )

            self.results.append(test_result)
            return test_result

        except Exception as e:
            duration = time.time() - start_time
            self.log_error(f"{name} failed with exception: {e}")

            test_result = TestResult(
                name=name,
                success=False,
                duration=duration,
                error=str(e)
            )

            self.results.append(test_result)
            return test_result

    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed."""
        self.log_section("Checking Dependencies")

        required_packages = [
            'pytest',
            'pytest-cov',
            'pytest-mock',
            'black',
            'isort',
            'flake8',
            'mypy',
            'bandit',
            'safety',
            'freezegun'
        ]

        missing_packages = []

        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.log_success(f"{package} is installed")
            except ImportError:
                missing_packages.append(package)
                self.log_error(f"{package} is missing")

        if missing_packages:
            self.log_error(f"Missing packages: {', '.join(missing_packages)}")
            self.log_info("Run: pip install -r requirements-dev.txt")
            return False

        return True

    def run_unit_tests(self) -> bool:
        """Run unit tests."""
        self.log_section("Unit Tests")

        command = [
            sys.executable, '-m', 'pytest',
            'tests/test_ssh_profile.py',
            'tests/test_ssh_manager.py',
            '-v',
            '--tb=short'
        ]

        result = self.run_command(command, "Unit Tests")
        return result.success

    def run_integration_tests(self) -> bool:
        """Run integration tests."""
        self.log_section("Integration Tests")

        command = [
            sys.executable, '-m', 'pytest',
            'tests/test_integration.py',
            '-v',
            '--tb=short'
        ]

        result = self.run_command(command, "Integration Tests")
        return result.success

    def run_cli_tests(self) -> bool:
        """Run CLI tests."""
        self.log_section("CLI Tests")

        command = [
            sys.executable, '-m', 'pytest',
            'tests/test_cli.py',
            '-v',
            '--tb=short'
        ]

        result = self.run_command(command, "CLI Tests")
        return result.success

    def run_coverage_tests(self) -> bool:
        """Run tests with coverage reporting."""
        self.log_section("Coverage Tests")

        command = [
            sys.executable, '-m', 'pytest',
            'tests/',
            '--cov=ssh_manager',
            '--cov=ssh_gui',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-report=xml:coverage.xml',
            '--cov-fail-under=85',
            '-v'
        ]

        result = self.run_command(command, "Coverage Tests")

        if result.success:
            self.log_success("Coverage report generated in htmlcov/")

        return result.success

    def run_performance_tests(self) -> bool:
        """Run performance tests."""
        self.log_section("Performance Tests")

        command = [
            sys.executable, '-m', 'pytest',
            'tests/',
            '-m', 'slow',
            '--benchmark-only',
            '--benchmark-sort=mean',
            '--benchmark-json=benchmark-results.json',
            '-v'
        ]

        result = self.run_command(command, "Performance Tests")
        return result.success

    def run_linting(self) -> Dict[str, bool]:
        """Run all linting checks."""
        self.log_section("Code Quality Checks")

        linting_results = {}

        # Black formatting check
        command = ['black', '--check', '--diff', 'ssh_manager.py', 'ssh_gui.py', 'tests/']
        result = self.run_command(command, "Black Formatting Check")
        linting_results['black'] = result.success

        # isort import sorting check
        command = ['isort', '--check-only', '--diff', 'ssh_manager.py', 'ssh_gui.py', 'tests/']
        result = self.run_command(command, "Import Sorting Check")
        linting_results['isort'] = result.success

        # Flake8 style check
        command = ['flake8', 'ssh_manager.py', 'ssh_gui.py', 'tests/']
        result = self.run_command(command, "Flake8 Style Check")
        linting_results['flake8'] = result.success

        # MyPy type checking
        command = ['mypy', 'ssh_manager.py', 'ssh_gui.py', '--ignore-missing-imports']
        result = self.run_command(command, "MyPy Type Check")
        linting_results['mypy'] = result.success

        return linting_results

    def run_security_checks(self) -> Dict[str, bool]:
        """Run security checks."""
        self.log_section("Security Checks")

        security_results = {}

        # Bandit security check
        command = [
            'bandit', '-r', 'ssh_manager.py', 'ssh_gui.py',
            '-f', 'json', '-o', 'bandit-report.json'
        ]
        result = self.run_command(command, "Bandit Security Check")
        security_results['bandit'] = result.success

        # Safety dependency check
        command = ['safety', 'check', '--json', '--output', 'safety-report.json']
        result = self.run_command(command, "Safety Dependency Check")
        security_results['safety'] = result.success

        return security_results

    def run_functional_tests(self) -> bool:
        """Run functional tests by testing actual CLI usage."""
        self.log_section("Functional Tests")

        # Test basic CLI functionality
        test_commands = [
            ([sys.executable, 'ssh_manager.py', '--help'], "CLI Help"),
            ([sys.executable, 'ssh_gui.py', '--help'], "GUI Help"),
        ]

        all_passed = True
        for command, name in test_commands:
            result = self.run_command(command, name)
            if not result.success:
                all_passed = False

        return all_passed

    def generate_report(self) -> Dict:
        """Generate a comprehensive test report."""
        total_duration = time.time() - self.start_time

        passed_tests = [r for r in self.results if r.success]
        failed_tests = [r for r in self.results if not r.success]

        report = {
            'timestamp': datetime.now().isoformat(),
            'total_duration': total_duration,
            'total_tests': len(self.results),
            'passed_tests': len(passed_tests),
            'failed_tests': len(failed_tests),
            'success_rate': len(passed_tests) / len(self.results) if self.results else 0,
            'results': [
                {
                    'name': r.name,
                    'success': r.success,
                    'duration': r.duration,
                    'timestamp': r.timestamp.isoformat(),
                    'error': r.error if r.error else None
                }
                for r in self.results
            ]
        }

        return report

    def print_summary(self):
        """Print a test summary."""
        self.log_section("Test Summary")

        total_duration = time.time() - self.start_time
        passed_tests = [r for r in self.results if r.success]
        failed_tests = [r for r in self.results if not r.success]

        self.log(f"Total Tests: {len(self.results)}", Colors.BOLD)
        self.log_success(f"Passed: {len(passed_tests)}")

        if failed_tests:
            self.log_error(f"Failed: {len(failed_tests)}")
            self.log("\nFailed Tests:")
            for result in failed_tests:
                self.log_error(f"  - {result.name} ({result.duration:.2f}s)")
                if result.error:
                    self.log(f"    Error: {result.error}", Colors.RED)

        success_rate = len(passed_tests) / len(self.results) if self.results else 0
        color = Colors.GREEN if success_rate == 1.0 else Colors.YELLOW if success_rate > 0.8 else Colors.RED
        self.log(f"Success Rate: {success_rate:.1%}", color)
        self.log(f"Total Duration: {total_duration:.2f}s", Colors.BOLD)

        # Overall result
        if success_rate == 1.0:
            self.log_success("\n🎉 All tests passed! Ready for deployment.")
        elif success_rate > 0.8:
            self.log_warning("\n⚠️  Most tests passed, but some issues need attention.")
        else:
            self.log_error("\n❌ Multiple test failures. Please fix before proceeding.")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Test Runner for SSH Profile Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --unit             # Run only unit tests
  python run_tests.py --coverage         # Run tests with coverage
  python run_tests.py --performance      # Run performance tests
  python run_tests.py --report           # Generate comprehensive report
  python run_tests.py --fast             # Run fast tests only
  python run_tests.py --ci               # Run CI/CD pipeline tests
        """
    )

    # Test selection options
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--cli', action='store_true', help='Run CLI tests only')
    parser.add_argument('--coverage', action='store_true', help='Run tests with coverage')
    parser.add_argument('--performance', action='store_true', help='Run performance tests')
    parser.add_argument('--lint', action='store_true', help='Run linting checks only')
    parser.add_argument('--security', action='store_true', help='Run security checks only')
    parser.add_argument('--functional', action='store_true', help='Run functional tests only')

    # Combined test suites
    parser.add_argument('--fast', action='store_true',
                       help='Run fast tests (unit + lint)')
    parser.add_argument('--full', action='store_true',
                       help='Run all tests including performance')
    parser.add_argument('--ci', action='store_true',
                       help='Run CI/CD pipeline tests')

    # Output options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--no-color', action='store_true',
                       help='Disable colored output')
    parser.add_argument('--report', action='store_true',
                       help='Generate JSON report')
    parser.add_argument('--output', '-o', type=str,
                       help='Output report to file')

    # Utility options
    parser.add_argument('--check-deps', action='store_true',
                       help='Check dependencies only')

    args = parser.parse_args()

    # Initialize test runner
    runner = TestRunner(verbose=args.verbose, no_color=args.no_color)

    # Check dependencies first
    if args.check_deps:
        success = runner.check_dependencies()
        sys.exit(0 if success else 1)

    if not runner.check_dependencies():
        sys.exit(1)

    # Determine which tests to run
    run_all = not any([
        args.unit, args.integration, args.cli, args.coverage,
        args.performance, args.lint, args.security, args.functional,
        args.fast, args.full, args.ci
    ])

    success = True

    try:
        if args.fast:
            success &= runner.run_unit_tests()
            runner.run_linting()

        elif args.full:
            success &= runner.run_unit_tests()
            success &= runner.run_integration_tests()
            success &= runner.run_cli_tests()
            success &= runner.run_coverage_tests()
            success &= runner.run_performance_tests()
            runner.run_linting()
            runner.run_security_checks()
            success &= runner.run_functional_tests()

        elif args.ci:
            success &= runner.run_unit_tests()
            success &= runner.run_integration_tests()
            success &= runner.run_cli_tests()
            success &= runner.run_coverage_tests()
            linting_results = runner.run_linting()
            security_results = runner.run_security_checks()
            success &= runner.run_functional_tests()

            # CI requires all linting to pass
            success &= all(linting_results.values())

        else:
            # Individual test categories
            if args.unit or run_all:
                success &= runner.run_unit_tests()

            if args.integration or run_all:
                success &= runner.run_integration_tests()

            if args.cli or run_all:
                success &= runner.run_cli_tests()

            if args.coverage:
                success &= runner.run_coverage_tests()

            if args.performance:
                success &= runner.run_performance_tests()

            if args.lint or run_all:
                runner.run_linting()

            if args.security or run_all:
                runner.run_security_checks()

            if args.functional or run_all:
                success &= runner.run_functional_tests()

    except KeyboardInterrupt:
        runner.log_warning("\n\nTest run interrupted by user")
        success = False

    except Exception as e:
        runner.log_error(f"\n\nUnexpected error during test run: {e}")
        success = False

    finally:
        # Always print summary
        runner.print_summary()

        # Generate report if requested
        if args.report or args.output:
            report = runner.generate_report()

            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(report, f, indent=2)
                runner.log_success(f"Report saved to {args.output}")
            else:
                print("\n" + "="*60)
                print("DETAILED REPORT")
                print("="*60)
                print(json.dumps(report, indent=2))

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
