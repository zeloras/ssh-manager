#!/usr/bin/env python3
"""
Test Setup Validation Script for SSH Profile Manager

This script validates that the test environment is properly configured
and all dependencies are available for running the comprehensive test suite.

Usage:
    python validate_test_setup.py [--fix] [--verbose]

Options:
    --fix       Attempt to fix issues automatically
    --verbose   Show detailed output
"""

import argparse
import importlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

    @classmethod
    def disable(cls):
        """Disable colors for non-terminal output."""
        for attr in ['RED', 'GREEN', 'YELLOW', 'BLUE', 'CYAN', 'BOLD', 'END']:
            setattr(cls, attr, '')


class TestSetupValidator:
    """Validates test setup and environment configuration."""

    def __init__(self, verbose: bool = False, fix_issues: bool = False):
        self.verbose = verbose
        self.fix_issues = fix_issues
        self.issues: List[str] = []
        self.warnings: List[str] = []

        if not sys.stdout.isatty():
            Colors.disable()

    def log(self, message: str, color: str = Colors.END):
        """Log a message with optional color."""
        print(f"{color}{message}{Colors.END}")

    def log_success(self, message: str):
        """Log a success message."""
        self.log(f"✅ {message}", Colors.GREEN)

    def log_error(self, message: str):
        """Log an error message."""
        self.log(f"❌ {message}", Colors.RED)
        self.issues.append(message)

    def log_warning(self, message: str):
        """Log a warning message."""
        self.log(f"⚠️  {message}", Colors.YELLOW)
        self.warnings.append(message)

    def log_info(self, message: str):
        """Log an info message."""
        if self.verbose:
            self.log(f"ℹ️  {message}", Colors.BLUE)

    def log_section(self, title: str):
        """Log a section header."""
        separator = "=" * 60
        self.log(f"\n{separator}", Colors.CYAN)
        self.log(f"{title.center(60)}", Colors.CYAN + Colors.BOLD)
        self.log(f"{separator}", Colors.CYAN)

    def check_python_version(self) -> bool:
        """Check Python version compatibility."""
        self.log_section("Python Version Check")

        version = sys.version_info
        min_version = (3, 8)

        if version >= min_version:
            self.log_success(f"Python {version.major}.{version.minor}.{version.micro} (>= {min_version[0]}.{min_version[1]})")
            return True
        else:
            self.log_error(f"Python {version.major}.{version.minor}.{version.micro} is too old. Minimum required: {min_version[0]}.{min_version[1]}")
            return False

    def check_project_structure(self) -> bool:
        """Check project directory structure."""
        self.log_section("Project Structure Check")

        required_files = [
            'ssh_manager.py',
            'ssh_gui.py',
            'tests/__init__.py',
            'tests/conftest.py',
            'tests/test_ssh_profile.py',
            'tests/test_ssh_manager.py',
            'tests/test_cli.py',
            'tests/test_integration.py',
            'pytest.ini',
            'requirements-dev.txt',
            'pyproject.toml',
            'tox.ini',
            '.coveragerc'
        ]

        required_dirs = [
            'tests',
            'tests/data',
            'tests/fixtures',
            '.github',
            '.github/workflows'
        ]

        missing_files = []
        missing_dirs = []

        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
                self.log_error(f"Missing file: {file_path}")
            else:
                self.log_info(f"Found: {file_path}")

        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                missing_dirs.append(dir_path)
                self.log_error(f"Missing directory: {dir_path}")
            else:
                self.log_info(f"Found: {dir_path}")

        if not missing_files and not missing_dirs:
            self.log_success("All required files and directories present")
            return True

        if self.fix_issues:
            self.log_info("Attempting to create missing directories...")
            for dir_path in missing_dirs:
                try:
                    Path(dir_path).mkdir(parents=True, exist_ok=True)
                    self.log_success(f"Created directory: {dir_path}")
                except Exception as e:
                    self.log_error(f"Failed to create {dir_path}: {e}")

        return len(missing_files) == 0

    def check_dependencies(self) -> bool:
        """Check required dependencies."""
        self.log_section("Dependencies Check")

        # Core dependencies
        core_deps = [
            'pytest',
            'pytest_cov',
            'pytest_mock',
            'black',
            'isort',
            'flake8',
            'mypy',
            'bandit',
            'safety',
            'freezegun',
            'coverage'
        ]

        # Optional dependencies
        optional_deps = [
            'tox',
            'pre_commit',
            'build',
            'twine'
        ]

        missing_core = []
        missing_optional = []

        for dep in core_deps:
            try:
                importlib.import_module(dep)
                self.log_info(f"Found: {dep}")
            except ImportError:
                missing_core.append(dep)
                self.log_error(f"Missing core dependency: {dep}")

        for dep in optional_deps:
            try:
                importlib.import_module(dep)
                self.log_info(f"Found: {dep}")
            except ImportError:
                missing_optional.append(dep)
                self.log_warning(f"Missing optional dependency: {dep}")

        if not missing_core:
            self.log_success("All core dependencies available")

        if missing_optional:
            self.log_info(f"Optional dependencies missing: {', '.join(missing_optional)}")

        if self.fix_issues and missing_core:
            self.log_info("Attempting to install missing core dependencies...")
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '-r', 'requirements-dev.txt'
                ], check=True, capture_output=True)
                self.log_success("Dependencies installed successfully")
            except subprocess.CalledProcessError as e:
                self.log_error(f"Failed to install dependencies: {e}")

        return len(missing_core) == 0

    def check_test_files(self) -> bool:
        """Check test file integrity."""
        self.log_section("Test Files Check")

        test_files = [
            'tests/test_ssh_profile.py',
            'tests/test_ssh_manager.py',
            'tests/test_cli.py',
            'tests/test_integration.py'
        ]

        all_valid = True

        for test_file in test_files:
            if not Path(test_file).exists():
                self.log_error(f"Test file missing: {test_file}")
                all_valid = False
                continue

            try:
                # Try to compile the test file
                with open(test_file, 'r') as f:
                    content = f.read()

                compile(content, test_file, 'exec')

                # Check for basic test structure
                if 'def test_' in content or 'class Test' in content:
                    self.log_info(f"Valid test file: {test_file}")
                else:
                    self.log_warning(f"No tests found in: {test_file}")

            except SyntaxError as e:
                self.log_error(f"Syntax error in {test_file}: {e}")
                all_valid = False
            except Exception as e:
                self.log_error(f"Error reading {test_file}: {e}")
                all_valid = False

        if all_valid:
            self.log_success("All test files are valid")

        return all_valid

    def check_configuration_files(self) -> bool:
        """Check configuration file validity."""
        self.log_section("Configuration Files Check")

        config_files = {
            'pytest.ini': self._check_pytest_config,
            'pyproject.toml': self._check_pyproject_config,
            'tox.ini': self._check_tox_config,
            '.coveragerc': self._check_coverage_config
        }

        all_valid = True

        for config_file, checker in config_files.items():
            if not Path(config_file).exists():
                self.log_warning(f"Configuration file missing: {config_file}")
                continue

            try:
                if checker(config_file):
                    self.log_info(f"Valid configuration: {config_file}")
                else:
                    self.log_warning(f"Configuration issues in: {config_file}")
            except Exception as e:
                self.log_error(f"Error checking {config_file}: {e}")
                all_valid = False

        return all_valid

    def _check_pytest_config(self, file_path: str) -> bool:
        """Check pytest.ini configuration."""
        with open(file_path, 'r') as f:
            content = f.read()

        required_sections = ['tool:pytest']
        required_settings = ['testpaths', 'python_files', 'addopts']

        for section in required_sections:
            if f'[{section}]' not in content:
                self.log_warning(f"Missing section [{section}] in {file_path}")
                return False

        for setting in required_settings:
            if setting not in content:
                self.log_warning(f"Missing setting '{setting}' in {file_path}")

        return True

    def _check_pyproject_config(self, file_path: str) -> bool:
        """Check pyproject.toml configuration."""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                self.log_warning("Cannot validate TOML files (tomllib/tomli not available)")
                return True

        with open(file_path, 'rb') as f:
            try:
                config = tomllib.load(f)

                required_sections = ['build-system', 'project', 'tool.pytest.ini_options']

                for section in required_sections:
                    keys = section.split('.')
                    current = config

                    for key in keys:
                        if key not in current:
                            self.log_warning(f"Missing section '{section}' in {file_path}")
                            return False
                        current = current[key]

                return True

            except Exception as e:
                self.log_error(f"Invalid TOML in {file_path}: {e}")
                return False

    def _check_tox_config(self, file_path: str) -> bool:
        """Check tox.ini configuration."""
        with open(file_path, 'r') as f:
            content = f.read()

        required_sections = ['tox', 'testenv']

        for section in required_sections:
            if f'[{section}]' not in content:
                self.log_warning(f"Missing section [{section}] in {file_path}")
                return False

        return True

    def _check_coverage_config(self, file_path: str) -> bool:
        """Check .coveragerc configuration."""
        with open(file_path, 'r') as f:
            content = f.read()

        required_sections = ['run', 'report']

        for section in required_sections:
            if f'[{section}]' not in content:
                self.log_warning(f"Missing section [{section}] in {file_path}")
                return False

        return True

    def run_sample_tests(self) -> bool:
        """Run a sample test to verify the test environment."""
        self.log_section("Sample Test Execution")

        try:
            # Run a simple test to verify pytest works
            result = subprocess.run([
                sys.executable, '-m', 'pytest',
                'tests/test_ssh_profile.py::TestSSHProfileInitialization::test_basic_initialization',
                '-v'
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                self.log_success("Sample test execution successful")
                return True
            else:
                self.log_error(f"Sample test failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.log_error("Sample test timed out")
            return False
        except Exception as e:
            self.log_error(f"Error running sample test: {e}")
            return False

    def check_github_actions(self) -> bool:
        """Check GitHub Actions workflow files."""
        self.log_section("GitHub Actions Check")

        workflow_files = [
            '.github/workflows/ci.yml',
            '.github/workflows/release.yml'
        ]

        all_valid = True

        for workflow_file in workflow_files:
            if not Path(workflow_file).exists():
                self.log_warning(f"GitHub Actions workflow missing: {workflow_file}")
                continue

            try:
                with open(workflow_file, 'r') as f:
                    content = f.read()

                # Basic YAML structure check
                if 'name:' in content and 'on:' in content and 'jobs:' in content:
                    self.log_info(f"Valid workflow: {workflow_file}")
                else:
                    self.log_warning(f"Invalid workflow structure: {workflow_file}")
                    all_valid = False

            except Exception as e:
                self.log_error(f"Error reading {workflow_file}: {e}")
                all_valid = False

        return all_valid

    def generate_report(self) -> Dict:
        """Generate a validation report."""
        return {
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'issues_count': len(self.issues),
            'warnings_count': len(self.warnings),
            'issues': self.issues,
            'warnings': self.warnings,
            'status': 'PASS' if len(self.issues) == 0 else 'FAIL'
        }

    def run_all_checks(self) -> bool:
        """Run all validation checks."""
        self.log(f"{Colors.CYAN}{Colors.BOLD}SSH Profile Manager Test Setup Validation{Colors.END}")
        self.log(f"{Colors.CYAN}{'=' * 60}{Colors.END}\n")

        checks = [
            ("Python Version", self.check_python_version),
            ("Project Structure", self.check_project_structure),
            ("Dependencies", self.check_dependencies),
            ("Test Files", self.check_test_files),
            ("Configuration Files", self.check_configuration_files),
            ("GitHub Actions", self.check_github_actions),
            ("Sample Test", self.run_sample_tests)
        ]

        all_passed = True

        for check_name, check_func in checks:
            try:
                if not check_func():
                    all_passed = False
            except Exception as e:
                self.log_error(f"Error during {check_name} check: {e}")
                all_passed = False

        # Final summary
        self.log_section("Validation Summary")

        if all_passed and len(self.issues) == 0:
            self.log_success("🎉 All validation checks passed!")
            self.log_success("Your test environment is ready for development.")
        elif len(self.issues) == 0:
            self.log_warning("⚠️  Validation completed with warnings.")
            self.log_info("Your test environment should work, but consider addressing warnings.")
        else:
            self.log_error("❌ Validation failed with issues.")
            self.log_error("Please fix the issues before running tests.")

        if self.warnings:
            self.log(f"\n{Colors.YELLOW}Warnings ({len(self.warnings)}):{Colors.END}")
            for warning in self.warnings:
                self.log(f"  • {warning}", Colors.YELLOW)

        if self.issues:
            self.log(f"\n{Colors.RED}Issues ({len(self.issues)}):{Colors.END}")
            for issue in self.issues:
                self.log(f"  • {issue}", Colors.RED)

        # Next steps
        if len(self.issues) == 0:
            self.log(f"\n{Colors.GREEN}🚀 Next Steps:{Colors.END}")
            self.log("  1. Run tests: python run_tests.py")
            self.log("  2. Run with coverage: python run_tests.py --coverage")
            self.log("  3. Run full test suite: python run_tests.py --full")
            self.log("  4. Set up pre-commit hooks: pre-commit install")
        else:
            self.log(f"\n{Colors.YELLOW}🔧 Recommended Actions:{Colors.END}")
            self.log("  1. Install dependencies: pip install -r requirements-dev.txt")
            self.log("  2. Re-run validation: python validate_test_setup.py --fix")
            self.log("  3. Check project documentation for setup instructions")

        return all_passed and len(self.issues) == 0


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description="Validate SSH Profile Manager test setup",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--fix', action='store_true',
                       help='Attempt to fix issues automatically')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output')
    parser.add_argument('--no-color', action='store_true',
                       help='Disable colored output')

    args = parser.parse_args()

    if args.no_color:
        Colors.disable()

    validator = TestSetupValidator(verbose=args.verbose, fix_issues=args.fix)
    success = validator.run_all_checks()

    # Generate report
    report = validator.generate_report()

    if args.verbose:
        print(f"\n{Colors.CYAN}Validation Report:{Colors.END}")
        print(f"Status: {report['status']}")
        print(f"Issues: {report['issues_count']}")
        print(f"Warnings: {report['warnings_count']}")

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
