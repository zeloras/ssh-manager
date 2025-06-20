"""
Test package for SSH Profile Manager

This package contains comprehensive tests for both CLI and GUI components
of the SSH Profile Manager application.

Test Structure:
- test_ssh_profile.py: Tests for SSHProfile class
- test_ssh_manager.py: Tests for SSHManager class
- test_cli.py: Command line interface tests
- test_gui.py: GUI interface tests
- test_integration.py: Integration tests
- conftest.py: Shared test fixtures and configuration
"""

__version__ = "1.0.0"
__author__ = "SSH Profile Manager Team"

# Test categories
UNIT_TESTS = "unit"
INTEGRATION_TESTS = "integration"
CLI_TESTS = "cli"
GUI_TESTS = "gui"
SLOW_TESTS = "slow"
NETWORK_TESTS = "network"

# Test data paths
import os
TEST_DIR = os.path.dirname(__file__)
TEST_DATA_DIR = os.path.join(TEST_DIR, "data")
FIXTURES_DIR = os.path.join(TEST_DIR, "fixtures")
