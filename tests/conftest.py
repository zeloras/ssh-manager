"""
Pytest configuration and shared fixtures for SSH Profile Manager tests.

This module provides common fixtures, test data, and configuration
for all test modules in the SSH Profile Manager test suite.
"""

import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from unittest.mock import Mock, patch

import pytest
from freezegun import freeze_time

# Import the modules we're testing
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ssh_manager import SSHProfile, SSHManager


# Test Configuration
@pytest.fixture(scope="session")
def test_config():
    """Global test configuration."""
    return {
        "test_data_dir": Path(__file__).parent / "data",
        "fixtures_dir": Path(__file__).parent / "fixtures",
        "temp_dir": None,  # Will be set by temp_dir fixture
    }


# Temporary Directory Fixtures
@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_config_file(temp_dir):
    """Create a temporary config file path."""
    config_file = temp_dir / "test_profiles.json"
    return str(config_file)


@pytest.fixture
def temp_ssh_dir(temp_dir):
    """Create a temporary SSH directory structure."""
    ssh_dir = temp_dir / ".ssh"
    ssh_dir.mkdir()

    # Create dummy key files
    (ssh_dir / "id_rsa").touch()
    (ssh_dir / "id_rsa.pub").touch()
    (ssh_dir / "id_ed25519").touch()
    (ssh_dir / "id_ed25519.pub").touch()

    return ssh_dir


# Sample Data Fixtures
@pytest.fixture
def sample_profile_data():
    """Sample SSH profile data for testing."""
    return {
        "id": "test-profile-1",
        "name": "test-server",
        "host": "example.com",
        "username": "testuser",
        "port": 22,
        "private_key_path": "~/.ssh/id_rsa",
        "jump_host": None,
        "description": "Test server profile",
        "created_at": "2025-01-20T10:00:00Z",
        "last_used": None
    }


@pytest.fixture
def sample_profile(sample_profile_data):
    """Create a sample SSHProfile instance."""
    return SSHProfile.from_dict(sample_profile_data)


@pytest.fixture
def multiple_profiles_data():
    """Multiple SSH profiles for testing."""
    return [
        {
            "id": "prod-web-1",
            "name": "production-web",
            "host": "web.prod.example.com",
            "username": "deploy",
            "port": 22,
            "private_key_path": "~/.ssh/id_rsa_prod",
            "jump_host": None,
            "description": "Production web server",
            "created_at": "2025-01-20T10:00:00Z",
            "last_used": "2025-01-20T15:30:00Z"
        },
        {
            "id": "dev-api-1",
            "name": "development-api",
            "host": "api.dev.example.com",
            "username": "developer",
            "port": 2222,
            "private_key_path": "~/.ssh/id_rsa_dev",
            "jump_host": None,
            "description": "Development API server",
            "created_at": "2025-01-20T11:00:00Z",
            "last_used": None
        },
        {
            "id": "db-prod-1",
            "name": "database-server",
            "host": "db.internal.example.com",
            "username": "dbadmin",
            "port": 22,
            "private_key_path": "~/.ssh/id_rsa_db",
            "jump_host": "bastion@gateway.example.com",
            "description": "Database server via bastion",
            "created_at": "2025-01-20T12:00:00Z",
            "last_used": "2025-01-20T14:00:00Z"
        }
    ]


@pytest.fixture
def populated_config_file(temp_config_file, multiple_profiles_data):
    """Create a config file with sample profiles."""
    config_data = {
        "version": "1.0",
        "profiles": multiple_profiles_data
    }

    with open(temp_config_file, 'w') as f:
        json.dump(config_data, f, indent=2)

    return temp_config_file


# SSH Manager Fixtures
@pytest.fixture
def empty_ssh_manager(temp_config_file):
    """Create an empty SSH manager instance."""
    return SSHManager(config_file=temp_config_file)


@pytest.fixture
def populated_ssh_manager(populated_config_file):
    """Create an SSH manager with sample profiles."""
    return SSHManager(config_file=populated_config_file)


# Mock Fixtures
@pytest.fixture
def mock_subprocess():
    """Mock subprocess for testing SSH connections."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        yield mock_run


@pytest.fixture
def mock_os_path_exists():
    """Mock os.path.exists for file system testing."""
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        yield mock_exists


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent timestamps."""
    fixed_time = "2025-01-20T10:00:00Z"
    with freeze_time(fixed_time):
        yield datetime.fromisoformat(fixed_time.replace('Z', '+00:00'))


# CLI Testing Fixtures
@pytest.fixture
def cli_runner():
    """Create a CLI test runner."""
    from click.testing import CliRunner
    return CliRunner()


@pytest.fixture
def mock_argv():
    """Mock sys.argv for CLI testing."""
    original_argv = sys.argv.copy()
    yield
    sys.argv = original_argv


# File System Fixtures
@pytest.fixture
def mock_home_dir(temp_dir):
    """Mock home directory for testing."""
    home_dir = temp_dir / "home"
    home_dir.mkdir()

    # Create config directory structure
    config_dir = home_dir / ".config" / "ssh-manager"
    config_dir.mkdir(parents=True)

    # Create SSH directory
    ssh_dir = home_dir / ".ssh"
    ssh_dir.mkdir()

    with patch('os.path.expanduser') as mock_expand:
        mock_expand.side_effect = lambda path: str(home_dir) + path[1:] if path.startswith('~') else path
        yield home_dir


# JSON Test Data Fixtures
@pytest.fixture
def invalid_json_file(temp_dir):
    """Create a file with invalid JSON for testing error handling."""
    invalid_file = temp_dir / "invalid.json"
    invalid_file.write_text("{invalid json content")
    return str(invalid_file)


@pytest.fixture
def corrupted_profiles_file(temp_dir):
    """Create a corrupted profiles file for testing."""
    corrupted_file = temp_dir / "corrupted_profiles.json"
    corrupted_data = {
        "version": "1.0",
        "profiles": [
            {
                "name": "incomplete-profile",
                "host": "example.com"
                # Missing required fields
            }
        ]
    }

    with open(corrupted_file, 'w') as f:
        json.dump(corrupted_data, f)

    return str(corrupted_file)


# Performance Testing Fixtures
@pytest.fixture
def large_profile_dataset():
    """Generate a large dataset for performance testing."""
    profiles = []
    for i in range(1000):
        profile_data = {
            "id": f"profile-{i}",
            "name": f"server-{i:04d}",
            "host": f"server{i}.example.com",
            "username": f"user{i}",
            "port": 22 + (i % 100),
            "private_key_path": f"~/.ssh/id_rsa_{i}",
            "jump_host": f"jump{i % 5}.example.com" if i % 5 == 0 else None,
            "description": f"Auto-generated test server {i}",
            "created_at": "2025-01-20T10:00:00Z",
            "last_used": "2025-01-20T15:30:00Z" if i % 3 == 0 else None
        }
        profiles.append(profile_data)

    return profiles


# Network Testing Fixtures
@pytest.fixture
def mock_network_failure():
    """Mock network failure scenarios."""
    def side_effect(*args, **kwargs):
        from subprocess import CalledProcessError
        raise CalledProcessError(255, "ssh", "Connection refused")

    with patch('subprocess.run', side_effect=side_effect) as mock_run:
        yield mock_run


# Parametrized Test Data
@pytest.fixture(params=[
    ("simple", "test.com", "user", 22, None, None),
    ("with_port", "test.com", "user", 2222, None, None),
    ("with_key", "test.com", "user", 22, "~/.ssh/id_rsa", None),
    ("with_jump", "test.com", "user", 22, None, "jump@bastion.com"),
    ("full_config", "test.com", "user", 2222, "~/.ssh/id_rsa", "jump@bastion.com"),
])
def profile_variations(request):
    """Parametrized fixture for different profile configurations."""
    name, host, username, port, key_path, jump_host = request.param
    return {
        "name": name,
        "host": host,
        "username": username,
        "port": port,
        "private_key_path": key_path,
        "jump_host": jump_host,
        "description": f"Test profile: {name}"
    }


# Cleanup Fixtures
@pytest.fixture(autouse=True)
def cleanup_environment():
    """Automatically cleanup environment after each test."""
    # Setup
    original_cwd = os.getcwd()

    yield

    # Cleanup
    os.chdir(original_cwd)

    # Clear any environment variables that might have been set
    test_env_vars = [var for var in os.environ.keys() if var.startswith('SSH_MANAGER_')]
    for var in test_env_vars:
        os.environ.pop(var, None)


# Error Testing Fixtures
@pytest.fixture
def permission_denied_file(temp_dir):
    """Create a file with permission denied for testing."""
    if os.name != 'nt':  # Skip on Windows
        restricted_file = temp_dir / "restricted.json"
        restricted_file.touch()
        restricted_file.chmod(0o000)

        yield str(restricted_file)

        # Cleanup
        restricted_file.chmod(0o644)
    else:
        # On Windows, just return a non-existent path
        yield str(temp_dir / "nonexistent" / "file.json")


# Assertion Helpers
def assert_profile_equals(profile1: SSHProfile, profile2: SSHProfile):
    """Helper function to assert two profiles are equal."""
    assert profile1.name == profile2.name
    assert profile1.host == profile2.host
    assert profile1.username == profile2.username
    assert profile1.port == profile2.port
    assert profile1.private_key_path == profile2.private_key_path
    assert profile1.jump_host == profile2.jump_host
    assert profile1.description == profile2.description


def assert_ssh_command_valid(command: str):
    """Helper function to validate SSH command format."""
    assert command.startswith("ssh ")
    assert "@" in command
    parts = command.split()
    assert len(parts) >= 2
