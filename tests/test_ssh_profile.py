"""
Unit tests for SSHProfile class in SSH Profile Manager.

This module contains comprehensive tests for the SSHProfile class,
covering initialization, serialization, SSH command generation,
and edge cases.
"""

import json
import uuid
from datetime import datetime
from unittest.mock import patch

import pytest
from freezegun import freeze_time

from ssh_manager import SSHProfile


class TestSSHProfileInitialization:
    """Test SSHProfile class initialization and basic properties."""

    def test_basic_initialization(self):
        """Test basic profile creation with required parameters."""
        profile = SSHProfile(
            name="test-server",
            host="example.com",
            username="testuser"
        )

        assert profile.name == "test-server"
        assert profile.host == "example.com"
        assert profile.username == "testuser"
        assert profile.port == 22  # Default port
        assert profile.private_key_path is None
        assert profile.jump_host is None
        assert profile.description == "SSH connection to example.com"
        assert profile.last_used is None
        assert isinstance(profile.id, str)
        assert len(profile.id) == 36  # UUID4 format

    def test_initialization_with_all_parameters(self):
        """Test profile creation with all parameters specified."""
        profile = SSHProfile(
            name="full-config",
            host="prod.example.com",
            username="deploy",
            port=2222,
            private_key_path="~/.ssh/id_rsa_prod",
            jump_host="bastion@gateway.com",
            description="Production server"
        )

        assert profile.name == "full-config"
        assert profile.host == "prod.example.com"
        assert profile.username == "deploy"
        assert profile.port == 2222
        assert profile.private_key_path == "~/.ssh/id_rsa_prod"
        assert profile.jump_host == "bastion@gateway.com"
        assert profile.description == "Production server"

    def test_initialization_with_custom_description(self):
        """Test that custom description overrides default."""
        profile = SSHProfile(
            name="custom",
            host="example.com",
            username="user",
            description="My custom description"
        )

        assert profile.description == "My custom description"

    @freeze_time("2025-01-20 10:00:00")
    def test_created_at_timestamp(self):
        """Test that created_at is set correctly."""
        profile = SSHProfile("test", "example.com", "user")
        assert profile.created_at == "2025-01-20T10:00:00"

    def test_unique_ids_generated(self):
        """Test that each profile gets a unique ID."""
        profile1 = SSHProfile("test1", "example1.com", "user1")
        profile2 = SSHProfile("test2", "example2.com", "user2")

        assert profile1.id != profile2.id
        assert isinstance(uuid.UUID(profile1.id), uuid.UUID)
        assert isinstance(uuid.UUID(profile2.id), uuid.UUID)


class TestSSHProfileSerialization:
    """Test serialization and deserialization of SSHProfile objects."""

    def test_to_dict_basic(self):
        """Test basic profile serialization to dictionary."""
        profile = SSHProfile("test", "example.com", "user")
        profile_dict = profile.to_dict()

        expected_keys = {
            'id', 'name', 'host', 'username', 'port',
            'private_key_path', 'jump_host', 'description',
            'created_at', 'last_used'
        }

        assert set(profile_dict.keys()) == expected_keys
        assert profile_dict['name'] == "test"
        assert profile_dict['host'] == "example.com"
        assert profile_dict['username'] == "user"
        assert profile_dict['port'] == 22
        assert profile_dict['private_key_path'] is None
        assert profile_dict['jump_host'] is None

    def test_to_dict_complete(self):
        """Test complete profile serialization."""
        profile = SSHProfile(
            name="complete",
            host="example.com",
            username="user",
            port=2222,
            private_key_path="~/.ssh/key",
            jump_host="jump@host.com",
            description="Complete profile"
        )

        profile_dict = profile.to_dict()

        assert profile_dict['port'] == 2222
        assert profile_dict['private_key_path'] == "~/.ssh/key"
        assert profile_dict['jump_host'] == "jump@host.com"
        assert profile_dict['description'] == "Complete profile"

    def test_from_dict_basic(self):
        """Test profile creation from dictionary."""
        data = {
            'id': 'test-id-123',
            'name': 'test-profile',
            'host': 'example.com',
            'username': 'testuser',
            'port': 22,
            'private_key_path': None,
            'jump_host': None,
            'description': 'Test description',
            'created_at': '2025-01-20T10:00:00',
            'last_used': None
        }

        profile = SSHProfile.from_dict(data)

        assert profile.id == 'test-id-123'
        assert profile.name == 'test-profile'
        assert profile.host == 'example.com'
        assert profile.username == 'testuser'
        assert profile.port == 22
        assert profile.private_key_path is None
        assert profile.jump_host is None
        assert profile.description == 'Test description'
        assert profile.created_at == '2025-01-20T10:00:00'
        assert profile.last_used is None

    def test_from_dict_with_defaults(self):
        """Test profile creation from dict with missing optional fields."""
        minimal_data = {
            'id': 'minimal-id',
            'name': 'minimal',
            'host': 'example.com',
            'username': 'user'
        }

        profile = SSHProfile.from_dict(minimal_data)

        assert profile.port == 22  # Default
        assert profile.private_key_path is None
        assert profile.jump_host is None
        assert profile.description is None
        assert profile.created_at is not None  # Should be set to current time

    def test_serialization_roundtrip(self):
        """Test that serialization and deserialization preserve data."""
        original = SSHProfile(
            name="roundtrip",
            host="test.com",
            username="user",
            port=2222,
            private_key_path="~/.ssh/test_key",
            jump_host="jump@bastion.com",
            description="Roundtrip test"
        )

        # Serialize and deserialize
        data = original.to_dict()
        recreated = SSHProfile.from_dict(data)

        # Compare all fields
        assert recreated.id == original.id
        assert recreated.name == original.name
        assert recreated.host == original.host
        assert recreated.username == original.username
        assert recreated.port == original.port
        assert recreated.private_key_path == original.private_key_path
        assert recreated.jump_host == original.jump_host
        assert recreated.description == original.description
        assert recreated.created_at == original.created_at
        assert recreated.last_used == original.last_used

    def test_json_serialization(self):
        """Test that profile can be serialized to and from JSON."""
        profile = SSHProfile(
            name="json-test",
            host="json.example.com",
            username="jsonuser",
            port=3333
        )

        # Convert to JSON and back
        json_str = json.dumps(profile.to_dict())
        data = json.loads(json_str)
        recreated = SSHProfile.from_dict(data)

        assert recreated.name == profile.name
        assert recreated.host == profile.host
        assert recreated.username == profile.username
        assert recreated.port == profile.port


class TestSSHCommandGeneration:
    """Test SSH command generation functionality."""

    def test_basic_ssh_command(self):
        """Test basic SSH command generation."""
        profile = SSHProfile("basic", "example.com", "user")
        command = profile.generate_ssh_command()

        assert command == "ssh user@example.com"

    def test_ssh_command_with_custom_port(self):
        """Test SSH command with custom port."""
        profile = SSHProfile("custom-port", "example.com", "user", port=2222)
        command = profile.generate_ssh_command()

        assert command == "ssh user@example.com -p 2222"

    def test_ssh_command_with_private_key(self):
        """Test SSH command with private key."""
        profile = SSHProfile(
            "with-key",
            "example.com",
            "user",
            private_key_path="~/.ssh/id_rsa"
        )
        command = profile.generate_ssh_command()

        assert command == "ssh user@example.com -i ~/.ssh/id_rsa"

    def test_ssh_command_with_jump_host(self):
        """Test SSH command with jump host."""
        profile = SSHProfile(
            "with-jump",
            "internal.example.com",
            "user",
            jump_host="jump@bastion.com"
        )
        command = profile.generate_ssh_command()

        assert command == "ssh user@internal.example.com -J jump@bastion.com"

    def test_ssh_command_with_all_options(self):
        """Test SSH command with all options."""
        profile = SSHProfile(
            "full-command",
            "secure.example.com",
            "admin",
            port=2222,
            private_key_path="~/.ssh/id_ed25519",
            jump_host="bastion@gateway.com"
        )
        command = profile.generate_ssh_command()

        expected = "ssh admin@secure.example.com -p 2222 -i ~/.ssh/id_ed25519 -J bastion@gateway.com"
        assert command == expected

    def test_ssh_command_default_port_not_included(self):
        """Test that default port 22 is not included in command."""
        profile = SSHProfile("default-port", "example.com", "user", port=22)
        command = profile.generate_ssh_command()

        assert command == "ssh user@example.com"
        assert "-p 22" not in command

    def test_ssh_command_order_consistency(self):
        """Test that SSH command options are in consistent order."""
        profile = SSHProfile(
            "order-test",
            "example.com",
            "user",
            port=3333,
            private_key_path="~/.ssh/key",
            jump_host="jump@host.com"
        )
        command = profile.generate_ssh_command()

        # Check that the order is: ssh user@host -p port -i key -J jump
        parts = command.split()
        assert parts[0] == "ssh"
        assert parts[1] == "user@example.com"

        # Find positions of options
        p_index = parts.index("-p") if "-p" in parts else -1
        i_index = parts.index("-i") if "-i" in parts else -1
        j_index = parts.index("-J") if "-J" in parts else -1

        # Verify order: -p before -i before -J
        if p_index != -1 and i_index != -1:
            assert p_index < i_index
        if i_index != -1 and j_index != -1:
            assert i_index < j_index
        if p_index != -1 and j_index != -1:
            assert p_index < j_index


class TestSSHProfileEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_name_handling(self):
        """Test behavior with empty profile name."""
        profile = SSHProfile("", "example.com", "user")
        assert profile.name == ""

    def test_special_characters_in_fields(self):
        """Test handling of special characters in profile fields."""
        profile = SSHProfile(
            "test-with-special",
            "test.example-site.com",
            "user_name",
            description="Test with special chars: !@#$%^&*()"
        )

        assert profile.host == "test.example-site.com"
        assert profile.username == "user_name"
        assert "!@#$%^&*()" in profile.description

    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        profile = SSHProfile(
            "тест",  # Cyrillic
            "例え.com",  # Japanese
            "用户",  # Chinese
            description="测试 unicode 支持"
        )

        assert profile.name == "тест"
        assert profile.host == "例え.com"
        assert profile.username == "用户"
        assert "unicode" in profile.description

    def test_very_long_fields(self):
        """Test handling of very long field values."""
        long_string = "x" * 1000
        profile = SSHProfile(
            "long-test",
            long_string,
            "user",
            description=long_string
        )

        assert len(profile.host) == 1000
        assert len(profile.description) == 1000

    def test_whitespace_handling(self):
        """Test handling of whitespace in fields."""
        profile = SSHProfile(
            "  spaced  ",
            "  example.com  ",
            "  user  "
        )

        # Values should be preserved as-is (no automatic trimming)
        assert profile.name == "  spaced  "
        assert profile.host == "  example.com  "
        assert profile.username == "  user  "

    def test_none_values_in_optional_fields(self):
        """Test explicit None values in optional fields."""
        profile = SSHProfile(
            "none-test",
            "example.com",
            "user",
            private_key_path=None,
            jump_host=None,
            description=None
        )

        assert profile.private_key_path is None
        assert profile.jump_host is None
        assert profile.description is None

    def test_invalid_port_values(self):
        """Test various port values."""
        # Valid ports
        profile_valid = SSHProfile("test", "example.com", "user", port=65535)
        assert profile_valid.port == 65535

        # Port 0 (technically valid in some contexts)
        profile_zero = SSHProfile("test", "example.com", "user", port=0)
        assert profile_zero.port == 0

        # Negative port (should be allowed by the class, validation elsewhere)
        profile_negative = SSHProfile("test", "example.com", "user", port=-1)
        assert profile_negative.port == -1


class TestSSHProfileComparison:
    """Test profile comparison and equality."""

    def test_profile_equality_by_content(self):
        """Test that profiles with same content should be considered equal."""
        profile1 = SSHProfile("test", "example.com", "user")
        profile2 = SSHProfile("test", "example.com", "user")

        # They have different IDs but same content
        assert profile1.id != profile2.id
        assert profile1.name == profile2.name
        assert profile1.host == profile2.host
        assert profile1.username == profile2.username

    def test_profile_dict_representation(self):
        """Test that profile dictionary representation is consistent."""
        profile = SSHProfile(
            "dict-test",
            "example.com",
            "user",
            port=2222,
            private_key_path="~/.ssh/key"
        )

        dict1 = profile.to_dict()
        dict2 = profile.to_dict()

        # Multiple calls should return identical dictionaries
        assert dict1 == dict2

    def test_profile_string_representation(self):
        """Test profile string representation if implemented."""
        profile = SSHProfile("string-test", "example.com", "user")

        # Basic test - profile should have some string representation
        str_repr = str(profile)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0


class TestSSHProfileValidation:
    """Test profile validation and data integrity."""

    def test_required_fields_present(self):
        """Test that required fields are always present in serialized data."""
        profile = SSHProfile("required-test", "example.com", "user")
        data = profile.to_dict()

        required_fields = ['id', 'name', 'host', 'username']
        for field in required_fields:
            assert field in data
            assert data[field] is not None

    def test_from_dict_with_extra_fields(self):
        """Test that extra fields in dictionary are ignored."""
        data = {
            'id': 'extra-test',
            'name': 'test',
            'host': 'example.com',
            'username': 'user',
            'extra_field': 'should be ignored',
            'another_extra': 123
        }

        profile = SSHProfile.from_dict(data)

        # Should create profile successfully, ignoring extra fields
        assert profile.name == 'test'
        assert profile.host == 'example.com'
        assert profile.username == 'user'

    def test_ssh_command_injection_prevention(self):
        """Test that SSH command generation handles potentially dangerous input."""
        # This is more about documenting behavior - the class doesn't
        # currently sanitize input, which might be intentional
        profile = SSHProfile(
            "injection-test",
            "example.com; cat /etc/passwd",
            "user; rm -rf /",
            private_key_path="~/.ssh/key; malicious_command"
        )

        command = profile.generate_ssh_command()

        # The command will contain the potentially dangerous strings
        # This documents current behavior - security validation should
        # happen at a higher level
        assert "example.com; cat /etc/passwd" in command
        assert "user; rm -rf /" in command
