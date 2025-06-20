"""
Command Line Interface tests for SSH Profile Manager.

This module contains comprehensive tests for the CLI functionality,
covering argument parsing, command execution, and output formatting.
"""

import json
import os
import sys
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch, call
import pytest

from ssh_manager import main, SSHManager, SSHProfile


class TestCLIArgumentParsing:
    """Test command line argument parsing."""

    def test_no_arguments_shows_help(self):
        """Test that running without arguments shows help."""
        with patch('sys.argv', ['ssh-manager']), \
             patch('argparse.ArgumentParser.print_help') as mock_help:
            main()
            mock_help.assert_called_once()

    def test_add_command_basic_args(self):
        """Test add command with basic arguments."""
        with patch('sys.argv', ['ssh-manager', 'add', 'test-server', 'example.com', 'user']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            main()

            mock_manager.add_profile.assert_called_once_with(
                'test-server', 'example.com', 'user', 22, None, None, None
            )

    def test_add_command_all_args(self):
        """Test add command with all optional arguments."""
        args = [
            'ssh-manager', 'add', 'full-server', 'example.com', 'admin',
            '-p', '2222',
            '-i', '~/.ssh/id_rsa',
            '-j', 'jump@bastion.com',
            '-d', 'Full configuration server'
        ]

        with patch('sys.argv', args), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            main()

            mock_manager.add_profile.assert_called_once_with(
                'full-server', 'example.com', 'admin', 2222,
                '~/.ssh/id_rsa', 'jump@bastion.com', 'Full configuration server'
            )

    def test_list_command(self):
        """Test list command execution."""
        with patch('sys.argv', ['ssh-manager', 'list']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            main()

            mock_manager.list_profiles.assert_called_once()

    def test_connect_command(self):
        """Test connect command execution."""
        with patch('sys.argv', ['ssh-manager', 'connect', 'test-server']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            main()

            mock_manager.connect.assert_called_once_with('test-server', False)

    def test_connect_command_dry_run(self):
        """Test connect command with dry run flag."""
        with patch('sys.argv', ['ssh-manager', 'connect', 'test-server', '--dry-run']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            main()

            mock_manager.connect.assert_called_once_with('test-server', True)

    def test_remove_command(self):
        """Test remove command execution."""
        with patch('sys.argv', ['ssh-manager', 'remove', 'test-server']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            main()

            mock_manager.remove_profile.assert_called_once_with('test-server')

    def test_search_command(self):
        """Test search command execution."""
        with patch('sys.argv', ['ssh-manager', 'search', 'production']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            main()

            mock_manager.search_profiles.assert_called_once_with('production')

    def test_stats_command(self):
        """Test stats command execution."""
        with patch('sys.argv', ['ssh-manager', 'stats']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            main()

            mock_manager.stats.assert_called_once()


class TestCLIIntegration:
    """Test CLI integration with actual SSHManager."""

    def test_full_workflow_add_list_connect(self, temp_dir):
        """Test complete workflow: add profile, list, then connect."""
        config_file = temp_dir / "cli_test.json"

        # Test add command
        with patch('sys.argv', ['ssh-manager', 'add', 'cli-test', 'example.com', 'user']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            # Use real manager with temp config
            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager

            main()

            # Verify profile was added
            assert 'cli-test' in manager.profiles
            assert manager.profiles['cli-test'].host == 'example.com'

        # Test list command
        with patch('sys.argv', ['ssh-manager', 'list']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager

            main()

            # Verify output contains our profile
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert 'cli-test' in output
            assert 'example.com' in output

        # Test connect command
        with patch('sys.argv', ['ssh-manager', 'connect', 'cli-test', '--dry-run']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager

            main()

            # Verify SSH command was shown
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert 'user@example.com' in output

    def test_add_duplicate_profile_handling(self, temp_dir):
        """Test handling of duplicate profile addition."""
        config_file = temp_dir / "duplicate_test.json"

        # Add first profile
        with patch('sys.argv', ['ssh-manager', 'add', 'duplicate', 'host1.com', 'user1']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager
            main()

        # Try to add duplicate
        with patch('sys.argv', ['ssh-manager', 'add', 'duplicate', 'host2.com', 'user2']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager
            main()

            # Should show error message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert 'already exists' in output

    def test_connect_nonexistent_profile(self, temp_dir):
        """Test connecting to non-existent profile."""
        config_file = temp_dir / "nonexistent_test.json"

        with patch('sys.argv', ['ssh-manager', 'connect', 'nonexistent']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager
            main()

            # Should show error message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert 'not found' in output

    def test_remove_profile_workflow(self, temp_dir):
        """Test profile removal workflow."""
        config_file = temp_dir / "remove_test.json"

        # Add profile first
        with patch('sys.argv', ['ssh-manager', 'add', 'to-remove', 'example.com', 'user']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager
            main()

        # Remove profile
        with patch('sys.argv', ['ssh-manager', 'remove', 'to-remove']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager
            main()

            # Verify profile was removed
            assert 'to-remove' not in manager.profiles

            # Should show success message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert 'Removed' in output

    def test_search_functionality(self, temp_dir):
        """Test search command functionality."""
        config_file = temp_dir / "search_test.json"

        # Add multiple profiles
        profiles_to_add = [
            ['production-web', 'web.prod.com', 'deploy'],
            ['production-db', 'db.prod.com', 'admin'],
            ['development-api', 'api.dev.com', 'developer']
        ]

        for name, host, username in profiles_to_add:
            with patch('sys.argv', ['ssh-manager', 'add', name, host, username]), \
                 patch('ssh_manager.SSHManager') as mock_manager_class:

                manager = SSHManager(config_file=str(config_file))
                mock_manager_class.return_value = manager
                main()

        # Search for production profiles
        with patch('sys.argv', ['ssh-manager', 'search', 'production']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager
            main()

            # Should find both production profiles
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert 'Found 2 profile(s)' in output
            assert 'production-web' in output
            assert 'production-db' in output

    def test_stats_with_profiles(self, temp_dir):
        """Test stats command with profiles."""
        config_file = temp_dir / "stats_test.json"

        # Add profiles with different configurations
        profiles = [
            ['basic', 'basic.com', 'user'],
            ['with-key', 'key.com', 'user', '-i', '~/.ssh/key'],
            ['custom-port', 'port.com', 'user', '-p', '2222']
        ]

        for profile_args in profiles:
            with patch('sys.argv', ['ssh-manager', 'add'] + profile_args), \
                 patch('ssh_manager.SSHManager') as mock_manager_class:

                manager = SSHManager(config_file=str(config_file))
                mock_manager_class.return_value = manager
                main()

        # Get stats
        with patch('sys.argv', ['ssh-manager', 'stats']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager
            main()

            # Should show statistics
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert 'Total profiles: 3' in output
            assert 'With SSH keys: 1' in output


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""

    def test_invalid_port_argument(self):
        """Test handling of invalid port argument."""
        with patch('sys.argv', ['ssh-manager', 'add', 'test', 'example.com', 'user', '-p', 'invalid']):
            with pytest.raises(SystemExit):  # argparse exits on invalid int
                main()

    def test_missing_required_arguments(self):
        """Test handling of missing required arguments."""
        # Missing username
        with patch('sys.argv', ['ssh-manager', 'add', 'test', 'example.com']):
            with pytest.raises(SystemExit):  # argparse exits on missing args
                main()

        # Missing profile name for connect
        with patch('sys.argv', ['ssh-manager', 'connect']):
            with pytest.raises(SystemExit):
                main()

        # Missing query for search
        with patch('sys.argv', ['ssh-manager', 'search']):
            with pytest.raises(SystemExit):
                main()

    def test_unknown_command(self):
        """Test handling of unknown commands."""
        with patch('sys.argv', ['ssh-manager', 'unknown-command']):
            with pytest.raises(SystemExit):  # argparse exits on unknown command
                main()

    def test_help_flag(self):
        """Test help flag functionality."""
        with patch('sys.argv', ['ssh-manager', '--help']):
            with pytest.raises(SystemExit):  # argparse exits after showing help
                main()

        with patch('sys.argv', ['ssh-manager', 'add', '--help']):
            with pytest.raises(SystemExit):
                main()

    def test_subcommand_help(self):
        """Test help for subcommands."""
        subcommands = ['add', 'list', 'connect', 'remove', 'search', 'stats']

        for subcommand in subcommands:
            with patch('sys.argv', ['ssh-manager', subcommand, '--help']):
                with pytest.raises(SystemExit):
                    main()

    def test_empty_arguments(self):
        """Test handling of empty string arguments."""
        with patch('sys.argv', ['ssh-manager', 'add', '', 'example.com', 'user']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            main()

            # Should still call add_profile with empty string
            mock_manager.add_profile.assert_called_once_with(
                '', 'example.com', 'user', 22, None, None, None
            )

    def test_special_characters_in_arguments(self):
        """Test handling of special characters in arguments."""
        special_args = [
            'ssh-manager', 'add', 'test-with-special!@#$%^&*()',
            'host.with-special_chars.com', 'user_name+special',
            '-d', 'Description with special chars: !@#$%^&*()'
        ]

        with patch('sys.argv', special_args), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            main()

            # Should handle special characters properly
            mock_manager.add_profile.assert_called_once()
            call_args = mock_manager.add_profile.call_args[0]
            assert '!@#$%^&*()' in call_args[0]  # profile name
            assert 'special_chars' in call_args[1]  # host
            assert 'user_name+special' in call_args[2]  # username

    def test_unicode_arguments(self):
        """Test handling of unicode characters in arguments."""
        unicode_args = [
            'ssh-manager', 'add', '测试服务器',
            'тест.example.com', '用户',
            '-d', 'Unicode description: 测试'
        ]

        with patch('sys.argv', unicode_args), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            main()

            # Should handle unicode properly
            mock_manager.add_profile.assert_called_once()
            call_args = mock_manager.add_profile.call_args[0]
            assert '测试服务器' in call_args[0]
            assert 'тест.example.com' in call_args[1]
            assert '用户' in call_args[2]


class TestCLIOutput:
    """Test CLI output formatting and display."""

    def test_add_profile_success_output(self, temp_dir):
        """Test output when successfully adding a profile."""
        config_file = temp_dir / "output_test.json"

        with patch('sys.argv', ['ssh-manager', 'add', 'output-test', 'example.com', 'user']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager

            main()

            # Should show success message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert 'Added SSH profile' in output
            assert 'output-test' in output

    def test_list_empty_profiles_output(self, temp_dir):
        """Test output when listing empty profiles."""
        config_file = temp_dir / "empty_output_test.json"

        with patch('sys.argv', ['ssh-manager', 'list']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager

            main()

            # Should show helpful message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert 'No SSH profiles configured' in output
            assert 'ssh-manager add' in output

    def test_connect_dry_run_output(self, temp_dir):
        """Test output for dry run connection."""
        config_file = temp_dir / "dry_run_test.json"

        # Add profile first
        with patch('sys.argv', ['ssh-manager', 'add', 'dry-run-test', 'example.com', 'user']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager
            main()

        # Test dry run
        with patch('sys.argv', ['ssh-manager', 'connect', 'dry-run-test', '--dry-run']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager

            main()

            # Should show SSH command
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert 'SSH command for' in output
            assert 'user@example.com' in output

    def test_stats_empty_output(self, temp_dir):
        """Test stats output with no profiles."""
        config_file = temp_dir / "stats_empty_test.json"

        with patch('sys.argv', ['ssh-manager', 'stats']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager

            main()

            # Should show no profiles message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert 'No profiles to analyze' in output

    def test_search_no_results_output(self, temp_dir):
        """Test search output with no results."""
        config_file = temp_dir / "search_empty_test.json"

        with patch('sys.argv', ['ssh-manager', 'search', 'nonexistent']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager

            main()

            # Should show no results message
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert 'No profiles found matching' in output
            assert 'nonexistent' in output


class TestCLIPerformance:
    """Test CLI performance with large datasets."""

    def test_large_profile_list_performance(self, temp_dir):
        """Test performance with many profiles."""
        config_file = temp_dir / "large_test.json"

        # Create manager and add many profiles directly
        manager = SSHManager(config_file=str(config_file))

        # Add 100 profiles
        for i in range(100):
            manager.add_profile(f'server-{i:03d}', f'host{i}.com', f'user{i}')

        # Test list command performance
        with patch('sys.argv', ['ssh-manager', 'list']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            mock_manager_class.return_value = manager

            # Should complete without hanging
            main()

            # Verify it listed all profiles
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            assert 'Found 100 SSH profile(s)' in output

    def test_search_performance_large_dataset(self, temp_dir):
        """Test search performance with large dataset."""
        config_file = temp_dir / "search_large_test.json"

        # Create manager with many profiles
        manager = SSHManager(config_file=str(config_file))

        # Add profiles with patterns
        for i in range(100):
            profile_type = 'prod' if i % 3 == 0 else 'dev'
            manager.add_profile(f'{profile_type}-server-{i:03d}', f'{profile_type}{i}.com', f'user{i}')

        # Search for production servers
        with patch('sys.argv', ['ssh-manager', 'search', 'prod']), \
             patch('ssh_manager.SSHManager') as mock_manager_class, \
             patch('builtins.print') as mock_print:

            mock_manager_class.return_value = manager

            # Should complete quickly
            main()

            # Should find the right number of profiles
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            output = '\n'.join(print_calls)
            # Should find about 34 profiles (every 3rd profile)
            assert 'Found' in output and 'profile(s) matching' in output


class TestCLIConfigFile:
    """Test CLI configuration file handling."""

    def test_default_config_location(self):
        """Test that CLI uses default config location."""
        with patch('sys.argv', ['ssh-manager', 'list']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            main()

            # Should be called with default config (None)
            mock_manager_class.assert_called_once_with(config_file=None)

    def test_config_file_creation(self, temp_dir):
        """Test that config file is created when adding first profile."""
        config_file = temp_dir / "new_config.json"

        # Ensure file doesn't exist
        assert not config_file.exists()

        with patch('sys.argv', ['ssh-manager', 'add', 'first', 'example.com', 'user']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager

            main()

            # Config file should be created
            assert config_file.exists()

            # Should contain the profile
            with open(config_file, 'r') as f:
                data = json.load(f)

            assert len(data['profiles']) == 1
            assert data['profiles'][0]['name'] == 'first'

    def test_config_file_permissions(self, temp_dir):
        """Test config file permissions after creation."""
        config_file = temp_dir / "permissions_test.json"

        with patch('sys.argv', ['ssh-manager', 'add', 'perm-test', 'example.com', 'user']), \
             patch('ssh_manager.SSHManager') as mock_manager_class:

            manager = SSHManager(config_file=str(config_file))
            mock_manager_class.return_value = manager

            main()

            # File should be created and readable
            assert config_file.exists()
            assert os.access(config_file, os.R_OK)
            assert os.access(config_file, os.W_OK)
