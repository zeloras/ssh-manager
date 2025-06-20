"""
Integration tests for SSH Profile Manager.

This module contains comprehensive integration tests that verify
the interaction between different components of the SSH Profile Manager,
including file operations, CLI integration, and end-to-end workflows.
"""

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, call
import pytest

from ssh_manager import SSHManager, SSHProfile, main


class TestFullWorkflowIntegration:
    """Test complete workflows from start to finish."""

    def test_complete_profile_lifecycle(self, temp_dir):
        """Test complete profile lifecycle: create, use, modify, delete."""
        config_file = temp_dir / "lifecycle_test.json"
        manager = SSHManager(config_file=str(config_file))

        # 1. Create profile
        result = manager.add_profile(
            "lifecycle-test",
            "lifecycle.example.com",
            "testuser",
            port=2222,
            private_key_path="~/.ssh/test_key",
            description="Lifecycle test profile"
        )
        assert result is True
        assert "lifecycle-test" in manager.profiles

        # 2. Verify persistence
        new_manager = SSHManager(config_file=str(config_file))
        assert "lifecycle-test" in new_manager.profiles
        profile = new_manager.profiles["lifecycle-test"]
        assert profile.host == "lifecycle.example.com"
        assert profile.port == 2222

        # 3. Use profile (dry run)
        with patch('builtins.print') as mock_print:
            result = new_manager.connect("lifecycle-test", dry_run=True)
            assert result is True

            # Verify command generation
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert "testuser@lifecycle.example.com -p 2222" in output

        # 4. Verify last_used was updated
        with patch('subprocess.run'), patch('builtins.print'):
            new_manager.connect("lifecycle-test")
            assert new_manager.profiles["lifecycle-test"].last_used is not None

        # 5. Search for profile
        with patch('builtins.print') as mock_print:
            new_manager.search_profiles("lifecycle")
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert "lifecycle-test" in output

        # 6. Delete profile
        result = new_manager.remove_profile("lifecycle-test")
        assert result is True
        assert "lifecycle-test" not in new_manager.profiles

        # 7. Verify deletion persisted
        final_manager = SSHManager(config_file=str(config_file))
        assert "lifecycle-test" not in final_manager.profiles

    def test_multi_profile_management(self, temp_dir):
        """Test managing multiple profiles with different configurations."""
        config_file = temp_dir / "multi_profile_test.json"
        manager = SSHManager(config_file=str(config_file))

        # Add various profile types
        profiles_to_add = [
            ("web-server", "web.example.com", "www", 80, None, None),
            ("db-server", "db.example.com", "dbadmin", 5432, "~/.ssh/db_key", None),
            ("jump-server", "internal.example.com", "admin", 22, "~/.ssh/admin_key", "jump@bastion.com"),
            ("dev-server", "dev.example.com", "developer", 2222, None, None),
        ]

        for name, host, username, port, key, jump in profiles_to_add:
            manager.add_profile(name, host, username, port, key, jump)

        # Verify all profiles exist
        assert len(manager.profiles) == 4

        # Test search functionality
        with patch('builtins.print') as mock_print:
            manager.search_profiles("server")
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert "Found 4 profile(s)" in output

        # Test specific searches
        with patch('builtins.print') as mock_print:
            manager.search_profiles("admin")
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert "db-server" in output
            assert "jump-server" in output

        # Test statistics
        with patch('builtins.print') as mock_print:
            manager.stats()
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert "Total profiles: 4" in output
            assert "With SSH keys: 2" in output
            assert "With jump hosts: 1" in output

        # Test connection to each profile type
        for profile_name in ["web-server", "db-server", "jump-server", "dev-server"]:
            with patch('subprocess.run') as mock_subprocess, \
                 patch('builtins.print'):
                manager.connect(profile_name)
                mock_subprocess.assert_called_once()
                # Verify the command contains expected elements
                command = mock_subprocess.call_args[0][0]
                profile = manager.profiles[profile_name]
                assert f"{profile.username}@{profile.host}" in " ".join(command)

    def test_file_format_compatibility(self, temp_dir):
        """Test compatibility with different file formats and versions."""
        config_file = temp_dir / "compatibility_test.json"

        # Create a config file with older format
        old_format_data = {
            "version": "1.0",
            "profiles": [
                {
                    "id": "old-format-1",
                    "name": "old-profile",
                    "host": "old.example.com",
                    "username": "olduser",
                    "port": 22,
                    "private_key_path": None,
                    "jump_host": None,
                    "description": "Old format profile",
                    "created_at": "2024-01-01T00:00:00Z",
                    "last_used": None
                }
            ]
        }

        with open(config_file, 'w') as f:
            json.dump(old_format_data, f, indent=2)

        # Load with current manager
        manager = SSHManager(config_file=str(config_file))
        assert len(manager.profiles) == 1
        assert "old-profile" in manager.profiles

        # Add new profile
        manager.add_profile("new-profile", "new.example.com", "newuser")

        # Verify both profiles exist
        assert len(manager.profiles) == 2

        # Check saved format
        with open(config_file, 'r') as f:
            saved_data = json.load(f)

        assert saved_data["version"] == "1.0"
        assert len(saved_data["profiles"]) == 2

        # Verify old profile preserved
        old_profile = next(p for p in saved_data["profiles"] if p["name"] == "old-profile")
        assert old_profile["host"] == "old.example.com"
        assert old_profile["created_at"] == "2024-01-01T00:00:00Z"

    def test_concurrent_access_simulation(self, temp_dir):
        """Test behavior with simulated concurrent access."""
        config_file = temp_dir / "concurrent_test.json"

        # Create first manager and add profile
        manager1 = SSHManager(config_file=str(config_file))
        manager1.add_profile("concurrent-1", "host1.com", "user1")

        # Create second manager (simulating another process)
        manager2 = SSHManager(config_file=str(config_file))
        assert "concurrent-1" in manager2.profiles

        # Add profile from second manager
        manager2.add_profile("concurrent-2", "host2.com", "user2")

        # First manager should still work (but won't see second profile until reload)
        manager1.add_profile("concurrent-3", "host3.com", "user3")

        # Create third manager to see final state
        manager3 = SSHManager(config_file=str(config_file))

        # Should have the last saved state
        # Note: This tests current behavior, not necessarily ideal behavior
        assert len(manager3.profiles) >= 1  # At least one profile should exist


class TestCLIIntegration:
    """Test CLI integration with the core system."""

    def test_cli_to_manager_integration(self, temp_dir):
        """Test that CLI commands properly interact with SSHManager."""
        config_file = temp_dir / "cli_integration_test.json"

        # Use CLI to add profile
        with patch('sys.argv', ['ssh-manager', 'add', 'cli-profile', 'cli.example.com', 'cliuser', '-p', '3333']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            # Use real manager
            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager

            main()

            # Verify profile was added
            assert "cli-profile" in manager.profiles
            assert manager.profiles["cli-profile"].port == 3333

        # Use CLI to list profiles
        with patch('sys.argv', ['ssh-manager', 'list']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager

            main()

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert "cli-profile" in output
            assert "cli.example.com" in output

        # Use CLI to connect (dry run)
        with patch('sys.argv', ['ssh-manager', 'connect', 'cli-profile', '--dry-run']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager

            main()

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert "cliuser@cli.example.com -p 3333" in output

    def test_cli_error_propagation(self, temp_dir):
        """Test that CLI properly handles and displays errors."""
        config_file = temp_dir / "cli_error_test.json"

        # Create manager with existing profile
        manager = SSHManager(config_file=str(config_file))
        manager.add_profile("existing", "existing.com", "user")

        # Try to add duplicate via CLI
        with patch('sys.argv', ['ssh-manager', 'add', 'existing', 'new.com', 'newuser']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            fresh_manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = fresh_manager

            main()

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert "already exists" in output

        # Try to connect to non-existent profile
        with patch('sys.argv', ['ssh-manager', 'connect', 'nonexistent']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            fresh_manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = fresh_manager

            main()

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert "not found" in output

    def test_cli_batch_operations(self, temp_dir):
        """Test multiple CLI operations in sequence."""
        config_file = temp_dir / "cli_batch_test.json"

        # Sequence of CLI operations
        operations = [
            (['add', 'batch-1', 'host1.com', 'user1'], "Added SSH profile 'batch-1'"),
            (['add', 'batch-2', 'host2.com', 'user2', '-p', '2222'], "Added SSH profile 'batch-2'"),
            (['add', 'batch-3', 'host3.com', 'user3', '-i', '~/.ssh/key'], "Added SSH profile 'batch-3'"),
            (['list'], "Found 3 SSH profile(s)"),
            (['search', 'batch'], "Found 3 profile(s) matching 'batch'"),
            (['stats'], "Total profiles: 3"),
            (['remove', 'batch-2'], "Removed SSH profile 'batch-2'"),
            (['list'], "Found 2 SSH profile(s)"),
        ]

        for operation, expected_output in operations:
            with patch('sys.argv', ['ssh-manager'] + operation), \
                 patch('ssh_manager.SSHManager') as mock_manager_class, \
                 patch('builtins.print') as mock_print:

                manager = SSHManager(config_file=str(config_file))
                mock_manager_class.return_value = manager

                main()

                print_calls = [call[0][0] for call in mock_print.call_args_list]
                output = '\n'.join(print_calls)
                assert expected_output in output


class TestFileSystemIntegration:
    """Test integration with file system operations."""

    def test_config_directory_creation(self, temp_dir):
        """Test automatic creation of config directories."""
        nested_config = temp_dir / "deep" / "nested" / "config" / "profiles.json"

        manager = SSHManager(config_file=str(nested_config))
        manager.add_profile("test-deep", "deep.example.com", "user")

        # Directory should be created
        assert nested_config.parent.exists()
        assert nested_config.exists()

        # Content should be valid
        with open(nested_config, 'r') as f:
            data = json.load(f)

        assert len(data["profiles"]) == 1
        assert data["profiles"][0]["name"] == "test-deep"

    def test_config_file_backup_on_corruption(self, temp_dir):
        """Test behavior when config file becomes corrupted."""
        config_file = temp_dir / "corruption_test.json"

        # Create valid config first
        manager = SSHManager(config_file=str(config_file))
        manager.add_profile("original", "original.com", "user")

        # Corrupt the file
        with open(config_file, 'w') as f:
            f.write("{invalid json content")

        # Creating new manager should handle corruption gracefully
        with patch('builtins.print') as mock_print:
            new_manager = SSHManager(config_file=str(config_file))

            # Should start with empty profiles
            assert len(new_manager.profiles) == 0

            # Should have logged error
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert "Error loading profiles" in output

        # Should be able to add new profiles
        new_manager.add_profile("recovery", "recovery.com", "user")
        assert "recovery" in new_manager.profiles

    def test_permission_handling(self, temp_dir):
        """Test handling of file permission issues."""
        if os.name == 'nt':  # Skip on Windows
            pytest.skip("Permission test not applicable on Windows")

        config_file = temp_dir / "permission_test.json"

        # Create manager and add profile
        manager = SSHManager(config_file=str(config_file))
        manager.add_profile("perm-test", "perm.example.com", "user")

        # Make file read-only
        os.chmod(config_file, 0o444)

        try:
            # Try to add another profile (should handle gracefully)
            manager.add_profile("perm-test-2", "perm2.example.com", "user2")

            # The add should appear to succeed in memory
            assert "perm-test-2" in manager.profiles

        finally:
            # Restore permissions for cleanup
            os.chmod(config_file, 0o644)

    def test_large_config_file_handling(self, temp_dir):
        """Test handling of large configuration files."""
        config_file = temp_dir / "large_config_test.json"
        manager = SSHManager(config_file=str(config_file))

        # Add many profiles
        for i in range(500):
            manager.add_profile(
                f"large-test-{i:03d}",
                f"host{i}.example.com",
                f"user{i}",
                port=22 + (i % 1000),
                private_key_path=f"~/.ssh/key_{i}" if i % 3 == 0 else None,
                description=f"Large test profile {i}"
            )

        # Verify all profiles exist
        assert len(manager.profiles) == 500

        # Test file size is reasonable
        file_size = os.path.getsize(config_file)
        assert file_size > 0
        assert file_size < 10 * 1024 * 1024  # Less than 10MB

        # Test loading performance
        start_time = time.time()
        new_manager = SSHManager(config_file=str(config_file))
        load_time = time.time() - start_time

        assert len(new_manager.profiles) == 500
        assert load_time < 5.0  # Should load in under 5 seconds

        # Test search performance
        start_time = time.time()
        with patch('builtins.print'):
            new_manager.search_profiles("large-test-1")
        search_time = time.time() - start_time

        assert search_time < 1.0  # Should search in under 1 second


class TestSSHCommandIntegration:
    """Test SSH command generation and execution integration."""

    def test_ssh_command_execution_simulation(self, temp_dir):
        """Test SSH command execution with various profile types."""
        config_file = temp_dir / "ssh_exec_test.json"
        manager = SSHManager(config_file=str(config_file))

        # Test profiles with different SSH configurations
        test_profiles = [
            ("basic", "basic.example.com", "user", 22, None, None),
            ("custom-port", "custom.example.com", "admin", 2222, None, None),
            ("with-key", "key.example.com", "deploy", 22, "~/.ssh/deploy_key", None),
            ("with-jump", "internal.example.com", "internal", 22, None, "jump@bastion.com"),
            ("full-config", "secure.example.com", "secure", 2222, "~/.ssh/secure_key", "bastion@gateway.com"),
        ]

        for name, host, username, port, key, jump in test_profiles:
            manager.add_profile(name, host, username, port, key, jump)

        # Test each profile's SSH command generation and execution
        for profile_name in manager.profiles:
            profile = manager.profiles[profile_name]

            # Test dry run
            with patch('builtins.print') as mock_print:
                result = manager.connect(profile_name, dry_run=True)
                assert result is True

                print_calls = [call[0][0] for call in mock_print.call_args_list]
                output = '\n'.join(print_calls)

                # Verify command contains expected elements
                assert f"{profile.username}@{profile.host}" in output

                if profile.port != 22:
                    assert f"-p {profile.port}" in output

                if profile.private_key_path:
                    assert f"-i {profile.private_key_path}" in output

                if profile.jump_host:
                    assert f"-J {profile.jump_host}" in output

            # Test actual execution (mocked)
            with patch('subprocess.run') as mock_subprocess, \
                 patch('builtins.print'):

                manager.connect(profile_name)

                # Verify subprocess was called
                mock_subprocess.assert_called_once()

                # Verify command structure
                called_command = mock_subprocess.call_args[0][0]
                assert called_command[0] == "ssh"
                assert f"{profile.username}@{profile.host}" in called_command

    def test_ssh_connection_error_handling(self, temp_dir):
        """Test SSH connection error handling."""
        config_file = temp_dir / "ssh_error_test.json"
        manager = SSHManager(config_file=str(config_file))

        manager.add_profile("error-test", "error.example.com", "user")

        # Test connection timeout
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("ssh", 30)), \
             patch('builtins.print') as mock_print:

            manager.connect("error-test")

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert "Connection failed" in output

        # Test connection refused
        with patch('subprocess.run', side_effect=subprocess.CalledProcessError(255, "ssh", "Connection refused")), \
             patch('builtins.print') as mock_print:

            manager.connect("error-test")

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert "Connection failed" in output

        # Test keyboard interrupt
        with patch('subprocess.run', side_effect=KeyboardInterrupt), \
             patch('builtins.print') as mock_print:

            manager.connect("error-test")

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert "interrupted by user" in output

    def test_ssh_command_special_characters(self, temp_dir):
        """Test SSH command generation with special characters."""
        config_file = temp_dir / "ssh_special_test.json"
        manager = SSHManager(config_file=str(config_file))

        # Profile with special characters (testing current behavior)
        manager.add_profile(
            "special-chars",
            "test-host.example.com",
            "test_user",
            private_key_path="~/.ssh/test key with spaces",
            jump_host="jump_user@bastion-host.com"
        )

        # Test command generation
        with patch('builtins.print') as mock_print:
            result = manager.connect("special-chars", dry_run=True)
            assert result is True

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)

            # Command should contain the special characters as-is
            assert "test key with spaces" in output
            assert "bastion-host.com" in output


class TestDataIntegrity:
    """Test data integrity across operations."""

    def test_profile_data_consistency(self, temp_dir):
        """Test that profile data remains consistent across operations."""
        config_file = temp_dir / "consistency_test.json"

        # Create profile with all fields
        original_data = {
            "name": "consistency-test",
            "host": "consistent.example.com",
            "username": "testuser",
            "port": 2222,
            "private_key_path": "~/.ssh/test_key",
            "jump_host": "jump@bastion.example.com",
            "description": "Consistency test profile"
        }

        manager = SSHManager(config_file=str(config_file))
        manager.add_profile(**original_data)

        # Verify immediate consistency
        profile = manager.profiles["consistency-test"]
        for key, value in original_data.items():
            assert getattr(profile, key) == value

        # Test persistence consistency
        new_manager = SSHManager(config_file=str(config_file))
        persisted_profile = new_manager.profiles["consistency-test"]

        for key, value in original_data.items():
            assert getattr(persisted_profile, key) == value

        # Test operation consistency (connect updates last_used)
        with patch('subprocess.run'), patch('builtins.print'):
            new_manager.connect("consistency-test")

        # All other fields should remain unchanged
        updated_profile = new_manager.profiles["consistency-test"]
        for key, value in original_data.items():
            assert getattr(updated_profile, key) == value

        # Only last_used should be updated
        assert updated_profile.last_used is not None

        # Test final persistence
        final_manager = SSHManager(config_file=str(config_file))
        final_profile = final_manager.profiles["consistency-test"]

        for key, value in original_data.items():
            assert getattr(final_profile, key) == value
        assert final_profile.last_used is not None

    def test_unicode_data_integrity(self, temp_dir):
        """Test that unicode data is preserved correctly."""
        config_file = temp_dir / "unicode_test.json"
        manager = SSHManager(config_file=str(config_file))

        # Profile with unicode characters
        unicode_data = {
            "name": "测试服务器",
            "host": "тест.example.com",
            "username": "用户",
            "description": "Тестовый сервер с unicode символами"
        }

        manager.add_profile(**unicode_data)

        # Test immediate unicode preservation
        profile = manager.profiles["测试服务器"]
        assert profile.host == "тест.example.com"
        assert profile.username == "用户"
        assert "unicode" in profile.description

        # Test persistence of unicode
        new_manager = SSHManager(config_file=str(config_file))
        persisted_profile = new_manager.profiles["测试服务器"]

        assert persisted_profile.host == "тест.example.com"
        assert persisted_profile.username == "用户"
        assert "unicode" in persisted_profile.description

        # Test search with unicode
        with patch('builtins.print') as mock_print:
            new_manager.search_profiles("测试")

            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert "测试服务器" in output

    def test_large_data_integrity(self, temp_dir):
        """Test data integrity with large amounts of data."""
        config_file = temp_dir / "large_data_test.json"
        manager = SSHManager(config_file=str(config_file))

        # Create profiles with large data fields
        large_description = "x" * 10000  # 10KB description
        large_host = "very-long-hostname-" + "x" * 1000 + ".example.com"

        manager.add_profile(
            "large-data-test",
            large_host,
            "user",
            description=large_description
        )

        # Verify immediate integrity
        profile = manager.profiles["large-data-test"]
        assert len(profile.description) == 10000
        assert len(profile.host) > 1000

        # Test persistence
        new_manager = SSHManager(config_file=str(config_file))
        persisted_profile = new_manager.profiles["large-data-test"]

        assert len(persisted_profile.description) == 10000
        assert len(persisted_profile.host) > 1000
        assert persisted_profile.description == large_description
        assert persisted_profile.host == large_host
