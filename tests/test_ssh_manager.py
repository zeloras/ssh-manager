"""
Unit tests for SSHManager class in SSH Profile Manager.

This module contains comprehensive tests for the SSHManager class,
covering profile management, file operations, search functionality,
and error handling.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, call
import pytest
from freezegun import freeze_time

from ssh_manager import SSHManager, SSHProfile


class TestSSHManagerInitialization:
    """Test SSHManager initialization and configuration."""

    def test_default_initialization(self):
        """Test default manager initialization."""
        with patch('os.path.expanduser') as mock_expand, \
             patch('os.makedirs') as mock_makedirs, \
             patch('os.path.exists', return_value=False):

            mock_expand.return_value = "/home/user/.config/ssh-manager"

            manager = SSHManager()

            mock_expand.assert_called_with("~/.config/ssh-manager")
            mock_makedirs.assert_called_with("/home/user/.config/ssh-manager", exist_ok=True)
            assert manager.config_file.endswith("profiles.json")
            assert len(manager.profiles) == 0

    def test_custom_config_file_initialization(self, temp_config_file):
        """Test initialization with custom config file."""
        manager = SSHManager(config_file=temp_config_file)

        assert manager.config_file == temp_config_file
        assert len(manager.profiles) == 0

    def test_initialization_loads_existing_profiles(self, populated_config_file):
        """Test that initialization loads existing profiles."""
        manager = SSHManager(config_file=populated_config_file)

        assert len(manager.profiles) == 3
        assert "production-web" in manager.profiles
        assert "development-api" in manager.profiles
        assert "database-server" in manager.profiles

    def test_initialization_with_invalid_json(self, invalid_json_file):
        """Test initialization with invalid JSON file."""
        with patch('builtins.print') as mock_print:
            manager = SSHManager(config_file=invalid_json_file)

            # Should handle error gracefully
            assert len(manager.profiles) == 0
            mock_print.assert_called()
            assert "Error loading profiles" in str(mock_print.call_args)

    def test_initialization_with_missing_file(self, temp_config_file):
        """Test initialization when config file doesn't exist."""
        # Remove the file if it exists
        if os.path.exists(temp_config_file):
            os.remove(temp_config_file)

        manager = SSHManager(config_file=temp_config_file)

        assert len(manager.profiles) == 0
        assert manager.config_file == temp_config_file


class TestSSHManagerProfileOperations:
    """Test basic profile CRUD operations."""

    def test_add_profile_success(self, empty_ssh_manager):
        """Test successful profile addition."""
        result = empty_ssh_manager.add_profile(
            "test-server",
            "example.com",
            "testuser"
        )

        assert result is True
        assert "test-server" in empty_ssh_manager.profiles

        profile = empty_ssh_manager.profiles["test-server"]
        assert profile.name == "test-server"
        assert profile.host == "example.com"
        assert profile.username == "testuser"
        assert profile.port == 22

    def test_add_profile_with_all_parameters(self, empty_ssh_manager):
        """Test profile addition with all parameters."""
        result = empty_ssh_manager.add_profile(
            "full-config",
            "prod.example.com",
            "deploy",
            port=2222,
            private_key_path="~/.ssh/id_rsa_prod",
            jump_host="bastion@gateway.com",
            description="Production server"
        )

        assert result is True
        profile = empty_ssh_manager.profiles["full-config"]
        assert profile.port == 2222
        assert profile.private_key_path == "~/.ssh/id_rsa_prod"
        assert profile.jump_host == "bastion@gateway.com"
        assert profile.description == "Production server"

    def test_add_duplicate_profile(self, empty_ssh_manager):
        """Test adding profile with duplicate name."""
        # Add first profile
        empty_ssh_manager.add_profile("duplicate", "example.com", "user")

        with patch('builtins.print') as mock_print:
            result = empty_ssh_manager.add_profile("duplicate", "other.com", "user2")

            assert result is False
            mock_print.assert_called_with("❌ Profile 'duplicate' already exists!")

        # Original profile should remain unchanged
        profile = empty_ssh_manager.profiles["duplicate"]
        assert profile.host == "example.com"
        assert profile.username == "user"

    def test_remove_profile_success(self, populated_ssh_manager):
        """Test successful profile removal."""
        assert "production-web" in populated_ssh_manager.profiles

        with patch('builtins.print') as mock_print:
            result = populated_ssh_manager.remove_profile("production-web")

            assert result is True
            assert "production-web" not in populated_ssh_manager.profiles
            mock_print.assert_called_with("🗑️  Removed SSH profile 'production-web'")

    def test_remove_nonexistent_profile(self, populated_ssh_manager):
        """Test removing non-existent profile."""
        with patch('builtins.print') as mock_print:
            result = populated_ssh_manager.remove_profile("nonexistent")

            assert result is False
            mock_print.assert_called_with("❌ Profile 'nonexistent' not found!")

    def test_profile_persistence_after_add(self, empty_ssh_manager):
        """Test that profiles are saved after addition."""
        with patch.object(empty_ssh_manager, 'save_profiles') as mock_save:
            empty_ssh_manager.add_profile("persist-test", "example.com", "user")
            mock_save.assert_called_once()

    def test_profile_persistence_after_remove(self, populated_ssh_manager):
        """Test that profiles are saved after removal."""
        with patch.object(populated_ssh_manager, 'save_profiles') as mock_save:
            populated_ssh_manager.remove_profile("production-web")
            mock_save.assert_called_once()


class TestSSHManagerFileOperations:
    """Test file loading and saving operations."""

    def test_save_profiles_creates_directory(self, temp_dir):
        """Test that save_profiles creates necessary directories."""
        config_file = temp_dir / "new_dir" / "profiles.json"
        manager = SSHManager(config_file=str(config_file))

        manager.add_profile("test", "example.com", "user")

        assert config_file.exists()
        assert config_file.parent.exists()

    def test_save_profiles_format(self, empty_ssh_manager, temp_config_file):
        """Test the format of saved profiles."""
        empty_ssh_manager.add_profile(
            "format-test",
            "example.com",
            "user",
            port=2222,
            description="Test format"
        )

        # Read the saved file
        with open(temp_config_file, 'r') as f:
            data = json.load(f)

        assert data['version'] == '1.0'
        assert 'profiles' in data
        assert len(data['profiles']) == 1

        profile_data = data['profiles'][0]
        assert profile_data['name'] == 'format-test'
        assert profile_data['host'] == 'example.com'
        assert profile_data['username'] == 'user'
        assert profile_data['port'] == 2222

    def test_load_profiles_from_file(self, temp_dir):
        """Test loading profiles from existing file."""
        config_file = temp_dir / "load_test.json"

        # Create test data
        test_data = {
            "version": "1.0",
            "profiles": [
                {
                    "id": "load-test-1",
                    "name": "load-test",
                    "host": "load.example.com",
                    "username": "loaduser",
                    "port": 22,
                    "private_key_path": None,
                    "jump_host": None,
                    "description": "Load test profile",
                    "created_at": "2025-01-20T10:00:00Z",
                    "last_used": None
                }
            ]
        }

        with open(config_file, 'w') as f:
            json.dump(test_data, f)

        # Load profiles
        manager = SSHManager(config_file=str(config_file))

        assert len(manager.profiles) == 1
        assert "load-test" in manager.profiles

        profile = manager.profiles["load-test"]
        assert profile.host == "load.example.com"
        assert profile.username == "loaduser"

    def test_load_profiles_handles_missing_fields(self, temp_dir):
        """Test loading profiles with missing optional fields."""
        config_file = temp_dir / "missing_fields.json"

        # Create data with missing optional fields
        test_data = {
            "version": "1.0",
            "profiles": [
                {
                    "id": "minimal-1",
                    "name": "minimal",
                    "host": "minimal.com",
                    "username": "user"
                    # Missing port, keys, etc.
                }
            ]
        }

        with open(config_file, 'w') as f:
            json.dump(test_data, f)

        manager = SSHManager(config_file=str(config_file))

        assert len(manager.profiles) == 1
        profile = manager.profiles["minimal"]
        assert profile.port == 22  # Default value
        assert profile.private_key_path is None

    def test_save_load_roundtrip(self, empty_ssh_manager):
        """Test that save/load operations preserve data."""
        # Add multiple profiles
        empty_ssh_manager.add_profile("server1", "host1.com", "user1")
        empty_ssh_manager.add_profile(
            "server2", "host2.com", "user2",
            port=2222, private_key_path="~/.ssh/key"
        )

        config_file = empty_ssh_manager.config_file

        # Create new manager with same config file
        new_manager = SSHManager(config_file=config_file)

        assert len(new_manager.profiles) == 2
        assert "server1" in new_manager.profiles
        assert "server2" in new_manager.profiles

        profile2 = new_manager.profiles["server2"]
        assert profile2.port == 2222
        assert profile2.private_key_path == "~/.ssh/key"


class TestSSHManagerConnectionOperations:
    """Test SSH connection functionality."""

    def test_connect_success(self, populated_ssh_manager, mock_subprocess):
        """Test successful SSH connection."""
        with patch('builtins.print') as mock_print:
            result = populated_ssh_manager.connect("production-web")

            assert result is None  # connect() doesn't return success/failure
            mock_subprocess.assert_called_once()

            # Check that subprocess was called with correct command
            call_args = mock_subprocess.call_args[0][0]  # First positional argument
            assert "deploy@web.prod.example.com" in " ".join(call_args)

    def test_connect_nonexistent_profile(self, populated_ssh_manager):
        """Test connecting to non-existent profile."""
        with patch('builtins.print') as mock_print, \
             patch.object(populated_ssh_manager, 'suggest_similar') as mock_suggest:

            result = populated_ssh_manager.connect("nonexistent")

            assert result is False
            mock_print.assert_called_with("❌ Profile 'nonexistent' not found!")
            mock_suggest.assert_called_with("nonexistent")

    def test_connect_dry_run(self, populated_ssh_manager):
        """Test dry run connection (show command only)."""
        with patch('builtins.print') as mock_print, \
             patch('subprocess.run') as mock_subprocess:

            result = populated_ssh_manager.connect("production-web", dry_run=True)

            assert result is True
            mock_subprocess.assert_not_called()  # Should not execute

            # Should print the command
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("SSH command for 'production-web'" in call for call in print_calls)

    @freeze_time("2025-01-20 15:30:00")
    def test_connect_updates_last_used(self, populated_ssh_manager, mock_subprocess):
        """Test that connection updates last_used timestamp."""
        profile = populated_ssh_manager.profiles["production-web"]
        original_last_used = profile.last_used

        populated_ssh_manager.connect("production-web")

        assert profile.last_used != original_last_used
        assert profile.last_used == "2025-01-20T15:30:00"

    def test_connect_keyboard_interrupt(self, populated_ssh_manager):
        """Test handling of keyboard interrupt during connection."""
        with patch('subprocess.run', side_effect=KeyboardInterrupt), \
             patch('builtins.print') as mock_print:

            populated_ssh_manager.connect("production-web")

            mock_print.assert_any_call("\n👋 Connection interrupted by user")

    def test_connect_subprocess_error(self, populated_ssh_manager):
        """Test handling of subprocess errors."""
        error_msg = "Connection failed"
        with patch('subprocess.run', side_effect=Exception(error_msg)), \
             patch('builtins.print') as mock_print:

            populated_ssh_manager.connect("production-web")

            mock_print.assert_any_call(f"❌ Connection failed: {error_msg}")


class TestSSHManagerSearchOperations:
    """Test search and suggestion functionality."""

    def test_search_profiles_by_name(self, populated_ssh_manager):
        """Test searching profiles by name."""
        with patch('builtins.print') as mock_print:
            populated_ssh_manager.search_profiles("production")

            # Should find "production-web"
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("Found 1 profile(s) matching 'production'" in call for call in print_calls)
            assert any("production-web" in call for call in print_calls)

    def test_search_profiles_by_host(self, populated_ssh_manager):
        """Test searching profiles by host."""
        with patch('builtins.print') as mock_print:
            populated_ssh_manager.search_profiles("dev.example")

            # Should find "development-api"
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("Found 1 profile(s) matching 'dev.example'" in call for call in print_calls)

    def test_search_profiles_by_username(self, populated_ssh_manager):
        """Test searching profiles by username."""
        with patch('builtins.print') as mock_print:
            populated_ssh_manager.search_profiles("deploy")

            # Should find profiles with "deploy" username
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("deploy@web.prod.example.com" in call for call in print_calls)

    def test_search_profiles_case_insensitive(self, populated_ssh_manager):
        """Test that search is case insensitive."""
        with patch('builtins.print') as mock_print:
            populated_ssh_manager.search_profiles("PRODUCTION")

            # Should still find "production-web"
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("production-web" in call for call in print_calls)

    def test_search_profiles_no_results(self, populated_ssh_manager):
        """Test search with no matching results."""
        with patch('builtins.print') as mock_print:
            populated_ssh_manager.search_profiles("nonexistent")

            mock_print.assert_called_with("🔍 No profiles found matching 'nonexistent'")

    def test_suggest_similar_exact_substring(self, populated_ssh_manager):
        """Test suggestion for profiles with substring match."""
        with patch('builtins.print') as mock_print:
            populated_ssh_manager.suggest_similar("prod")

            # Should suggest "production-web"
            mock_print.assert_called_with("💡 Did you mean: production-web?")

    def test_suggest_similar_multiple_matches(self, populated_ssh_manager):
        """Test suggestion with multiple similar profiles."""
        # Add another profile with similar name
        populated_ssh_manager.add_profile("production-api", "api.prod.com", "deploy")

        with patch('builtins.print') as mock_print:
            populated_ssh_manager.suggest_similar("prod")

            # Should suggest both profiles
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            suggestions = print_calls[-1]  # Last print call
            assert "production-web" in suggestions
            assert "production-api" in suggestions

    def test_suggest_similar_no_matches(self, populated_ssh_manager):
        """Test suggestion with no similar profiles."""
        with patch('builtins.print') as mock_print:
            populated_ssh_manager.suggest_similar("xyz123")

            # Should not call print (no suggestions)
            mock_print.assert_not_called()


class TestSSHManagerListOperations:
    """Test profile listing functionality."""

    def test_list_profiles_empty(self, empty_ssh_manager):
        """Test listing when no profiles exist."""
        with patch('builtins.print') as mock_print:
            empty_ssh_manager.list_profiles()

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("No SSH profiles configured" in call for call in print_calls)
            assert any("ssh-manager add" in call for call in print_calls)

    def test_list_profiles_populated(self, populated_ssh_manager):
        """Test listing with existing profiles."""
        with patch('builtins.print') as mock_print:
            populated_ssh_manager.list_profiles()

            print_calls = [call[0][0] for call in mock_print.call_args_list]

            # Should show count
            assert any("Found 3 SSH profile(s)" in call for call in print_calls)

            # Should list all profiles
            all_output = "\n".join(print_calls)
            assert "production-web" in all_output
            assert "development-api" in all_output
            assert "database-server" in all_output

            # Should show profile details
            assert "deploy@web.prod.example.com" in all_output
            assert "developer@api.dev.example.com" in all_output

    def test_list_profiles_shows_keys_and_jump_hosts(self, populated_ssh_manager):
        """Test that listing shows SSH keys and jump hosts when present."""
        with patch('builtins.print') as mock_print:
            populated_ssh_manager.list_profiles()

            all_output = "\n".join([call[0][0] for call in mock_print.call_args_list])

            # Should show key paths
            assert "~/.ssh/id_rsa_prod" in all_output
            assert "~/.ssh/id_rsa_dev" in all_output

            # Should show jump host
            assert "bastion@gateway.example.com" in all_output

    def test_list_profiles_numbering(self, populated_ssh_manager):
        """Test that profiles are numbered in listing."""
        with patch('builtins.print') as mock_print:
            populated_ssh_manager.list_profiles()

            all_output = "\n".join([call[0][0] for call in mock_print.call_args_list])

            # Should have numbered entries
            assert "1. 🖥️" in all_output
            assert "2. 🖥️" in all_output
            assert "3. 🖥️" in all_output


class TestSSHManagerStatistics:
    """Test statistics functionality."""

    def test_stats_empty(self, empty_ssh_manager):
        """Test statistics with no profiles."""
        with patch('builtins.print') as mock_print:
            empty_ssh_manager.stats()

            mock_print.assert_called_with("📊 No profiles to analyze")

    def test_stats_populated(self, populated_ssh_manager):
        """Test statistics with multiple profiles."""
        with patch('builtins.print') as mock_print:
            populated_ssh_manager.stats()

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            all_output = "\n".join(print_calls)

            # Should show total count
            assert "Total profiles: 3" in all_output

            # Should count profiles with keys
            assert "With SSH keys: 3" in all_output  # All test profiles have keys

            # Should count profiles with jump hosts
            assert "With jump hosts: 1" in all_output  # Only database-server has jump host

            # Should show most common port
            assert "Most common port: 22" in all_output

    def test_stats_port_distribution(self, empty_ssh_manager):
        """Test statistics port distribution calculation."""
        # Add profiles with different ports
        empty_ssh_manager.add_profile("server1", "host1.com", "user", port=22)
        empty_ssh_manager.add_profile("server2", "host2.com", "user", port=22)
        empty_ssh_manager.add_profile("server3", "host3.com", "user", port=2222)

        with patch('builtins.print') as mock_print:
            empty_ssh_manager.stats()

            all_output = "\n".join([call[0][0] for call in mock_print.call_args_list])

            # Port 22 should be most common (2 occurrences vs 1 for 2222)
            assert "Most common port: 22" in all_output

    def test_stats_feature_counting(self, empty_ssh_manager):
        """Test accurate counting of profile features."""
        # Add profiles with various features
        empty_ssh_manager.add_profile(
            "basic", "host1.com", "user"  # No key, no jump
        )
        empty_ssh_manager.add_profile(
            "with-key", "host2.com", "user",
            private_key_path="~/.ssh/key"  # Key, no jump
        )
        empty_ssh_manager.add_profile(
            "with-jump", "host3.com", "user",
            jump_host="jump@host.com"  # Jump, no key
        )
        empty_ssh_manager.add_profile(
            "full", "host4.com", "user",
            private_key_path="~/.ssh/key2",
            jump_host="jump2@host.com"  # Both key and jump
        )

        with patch('builtins.print') as mock_print:
            empty_ssh_manager.stats()

            all_output = "\n".join([call[0][0] for call in mock_print.call_args_list])

            assert "Total profiles: 4" in all_output
            assert "With SSH keys: 2" in all_output  # with-key and full
            assert "With jump hosts: 2" in all_output  # with-jump and full


class TestSSHManagerErrorHandling:
    """Test error handling and edge cases."""

    def test_load_profiles_json_decode_error(self, temp_dir):
        """Test handling of JSON decode errors."""
        config_file = temp_dir / "bad.json"
        config_file.write_text("{invalid json")

        with patch('builtins.print') as mock_print:
            manager = SSHManager(config_file=str(config_file))

            assert len(manager.profiles) == 0
            mock_print.assert_called()
            assert "Error loading profiles" in str(mock_print.call_args)

    def test_load_profiles_key_error(self, temp_dir):
        """Test handling of missing keys in profile data."""
        config_file = temp_dir / "missing_keys.json"

        # Create JSON with missing required fields
        bad_data = {
            "version": "1.0",
            "profiles": [
                {
                    "name": "incomplete"
                    # Missing host, username, etc.
                }
            ]
        }

        with open(config_file, 'w') as f:
            json.dump(bad_data, f)

        with patch('builtins.print') as mock_print:
            manager = SSHManager(config_file=str(config_file))

            # Should handle error gracefully
            assert len(manager.profiles) == 0
            mock_print.assert_called()

    def test_save_profiles_permission_error(self, permission_denied_file):
        """Test handling of permission errors during save."""
        if os.name == 'nt':  # Skip on Windows
            pytest.skip("Permission test not applicable on Windows")

        manager = SSHManager(config_file=permission_denied_file)
        manager.add_profile("test", "example.com", "user")

        # Should not raise exception, but may print error
        # The exact behavior depends on implementation

    def test_save_profiles_directory_creation_failure(self, temp_dir):
        """Test handling of directory creation failures."""
        # Try to create config in a location that can't be created
        impossible_path = temp_dir / "readonly" / "deep" / "path" / "profiles.json"

        # Make parent directory read-only (Unix only)
        if os.name != 'nt':
            readonly_dir = temp_dir / "readonly"
            readonly_dir.mkdir()
            readonly_dir.chmod(0o444)  # Read-only

            with patch('builtins.print'):  # Suppress error output
                manager = SSHManager(config_file=str(impossible_path))
                # Should not crash when trying to save
                try:
                    manager.add_profile("test", "example.com", "user")
                except Exception:
                    pass  # Expected to fail, but shouldn't crash

            # Cleanup
            readonly_dir.chmod(0o755)

    def test_empty_profile_name_in_operations(self, populated_ssh_manager):
        """Test operations with empty profile names."""
        with patch('builtins.print') as mock_print:
            result = populated_ssh_manager.connect("")
            assert result is False

            result = populated_ssh_manager.remove_profile("")
            assert result is False

    def test_none_profile_name_handling(self, populated_ssh_manager):
        """Test handling of None as profile name."""
        with pytest.raises((TypeError, AttributeError)):
            populated_ssh_manager.connect(None)

    def test_unicode_profile_operations(self, empty_ssh_manager):
        """Test operations with unicode characters."""
        # Add profile with unicode characters
        result = empty_ssh_manager.add_profile(
            "测试服务器",  # Chinese characters
            "тест.example.com",  # Cyrillic
            "用户"  # Chinese username
        )

        assert result is True
        assert "测试服务器" in empty_ssh_manager.profiles

        # Test connection
        with patch('subprocess.run') as mock_subprocess:
            empty_ssh_manager.connect("测试服务器")
            mock_subprocess.assert_called_once()

    def test_very_long_profile_names(self, empty_ssh_manager):
        """Test handling of very long profile names."""
        long_name = "x" * 1000

        result = empty_ssh_manager.add_profile(
            long_name,
            "example.com",
            "user"
        )

        assert result is True
        assert long_name in empty_ssh_manager.profiles

        # Should be able to connect
        with patch('subprocess.run'):
            result = empty_ssh_manager.connect(long_name, dry_run=True)
            assert result is True
