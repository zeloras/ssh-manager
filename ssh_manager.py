#!/usr/bin/env python3
"""
SSH Profile Manager - Standalone Terminal Tool
A simple SSH connection manager that can be used from any terminal.
"""

import json
import os
import sys
import subprocess
import argparse
from datetime import datetime
from typing import Dict, List, Optional
import uuid

class SSHProfile:
    def __init__(self, name: str, host: str, username: str, port: int = 22,
                 private_key_path: str = None, jump_host: str = None,
                 description: str = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.host = host
        self.username = username
        self.port = port
        self.private_key_path = private_key_path
        self.jump_host = jump_host
        self.description = description or f"SSH connection to {host}"
        self.created_at = datetime.now().isoformat()
        self.last_used = None

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'host': self.host,
            'username': self.username,
            'port': self.port,
            'private_key_path': self.private_key_path,
            'jump_host': self.jump_host,
            'description': self.description,
            'created_at': self.created_at,
            'last_used': self.last_used
        }

    @classmethod
    def from_dict(cls, data: Dict):
        profile = cls(
            name=data['name'],
            host=data['host'],
            username=data['username'],
            port=data.get('port', 22),
            private_key_path=data.get('private_key_path'),
            jump_host=data.get('jump_host'),
            description=data.get('description')
        )
        profile.id = data['id']
        profile.created_at = data.get('created_at', datetime.now().isoformat())
        profile.last_used = data.get('last_used')
        return profile

    def generate_ssh_command(self) -> str:
        """Generate SSH command for this profile"""
        cmd = f"ssh {self.username}@{self.host}"

        if self.port != 22:
            cmd += f" -p {self.port}"

        if self.private_key_path:
            cmd += f" -i {self.private_key_path}"

        if self.jump_host:
            cmd += f" -J {self.jump_host}"

        return cmd

class SSHManager:
    def __init__(self, config_file: str = None):
        if config_file is None:
            config_dir = os.path.expanduser("~/.config/ssh-manager")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "profiles.json")

        self.config_file = config_file
        self.profiles: Dict[str, SSHProfile] = {}
        self.load_profiles()

    def load_profiles(self):
        """Load profiles from config file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for profile_data in data.get('profiles', []):
                        profile = SSHProfile.from_dict(profile_data)
                        self.profiles[profile.name] = profile
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading profiles: {e}")

    def save_profiles(self):
        """Save profiles to config file"""
        data = {
            'version': '1.0',
            'profiles': [profile.to_dict() for profile in self.profiles.values()]
        }

        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_profile(self, name: str, host: str, username: str, port: int = 22,
                   private_key_path: str = None, jump_host: str = None,
                   description: str = None) -> bool:
        """Add a new SSH profile"""
        if name in self.profiles:
            print(f"❌ Profile '{name}' already exists!")
            return False

        profile = SSHProfile(name, host, username, port, private_key_path,
                           jump_host, description)
        self.profiles[name] = profile
        self.save_profiles()
        print(f"✅ Added SSH profile '{name}'")
        return True

    def list_profiles(self):
        """List all SSH profiles"""
        if not self.profiles:
            print("📝 No SSH profiles configured.")
            print("\nUse 'ssh-manager add <name> <host> <username>' to create your first profile.")
            return

        print(f"📋 Found {len(self.profiles)} SSH profile(s):\n")

        for i, (name, profile) in enumerate(self.profiles.items(), 1):
            print(f"{i}. 🖥️  {profile.name}")
            print(f"   • Host: {profile.username}@{profile.host}:{profile.port}")
            if profile.private_key_path:
                print(f"   • Key: {profile.private_key_path}")
            if profile.jump_host:
                print(f"   • Jump: {profile.jump_host}")
            print(f"   • Description: {profile.description}")
            print()

    def connect(self, name: str, dry_run: bool = False):
        """Connect to SSH profile"""
        if name not in self.profiles:
            print(f"❌ Profile '{name}' not found!")
            self.suggest_similar(name)
            return False

        profile = self.profiles[name]
        ssh_cmd = profile.generate_ssh_command()

        if dry_run:
            print(f"🔧 SSH command for '{name}':")
            print(f"   {ssh_cmd}")
            return True

        print(f"🚀 Connecting to {profile.name}...")
        print(f"💻 Command: {ssh_cmd}")

        # Update last used timestamp
        profile.last_used = datetime.now().isoformat()
        self.save_profiles()

        # Execute SSH command
        try:
            subprocess.run(ssh_cmd.split())
        except KeyboardInterrupt:
            print("\n👋 Connection interrupted by user")
        except Exception as e:
            print(f"❌ Connection failed: {e}")

    def remove_profile(self, name: str) -> bool:
        """Remove SSH profile"""
        if name not in self.profiles:
            print(f"❌ Profile '{name}' not found!")
            return False

        del self.profiles[name]
        self.save_profiles()
        print(f"🗑️  Removed SSH profile '{name}'")
        return True

    def search_profiles(self, query: str):
        """Search profiles by name, host, or username"""
        results = []
        query_lower = query.lower()

        for profile in self.profiles.values():
            if (query_lower in profile.name.lower() or
                query_lower in profile.host.lower() or
                query_lower in profile.username.lower()):
                results.append(profile)

        if not results:
            print(f"🔍 No profiles found matching '{query}'")
            return

        print(f"🔍 Found {len(results)} profile(s) matching '{query}':\n")
        for i, profile in enumerate(results, 1):
            print(f"{i}. {profile.name} ({profile.username}@{profile.host})")

    def suggest_similar(self, name: str):
        """Suggest similar profile names"""
        suggestions = []
        for profile_name in self.profiles.keys():
            if name.lower() in profile_name.lower() or profile_name.lower() in name.lower():
                suggestions.append(profile_name)

        if suggestions:
            print(f"💡 Did you mean: {', '.join(suggestions)}?")

    def stats(self):
        """Show statistics about profiles"""
        total = len(self.profiles)
        if total == 0:
            print("📊 No profiles to analyze")
            return

        with_keys = sum(1 for p in self.profiles.values() if p.private_key_path)
        with_jump = sum(1 for p in self.profiles.values() if p.jump_host)

        ports = {}
        for profile in self.profiles.values():
            ports[profile.port] = ports.get(profile.port, 0) + 1

        most_common_port = max(ports.items(), key=lambda x: x[1])[0] if ports else 22

        print("📊 SSH Profile Statistics:")
        print(f"   • Total profiles: {total}")
        print(f"   • With SSH keys: {with_keys}")
        print(f"   • With jump hosts: {with_jump}")
        print(f"   • Most common port: {most_common_port}")

def main():
    parser = argparse.ArgumentParser(description="SSH Profile Manager - Simple terminal SSH connection manager")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add profile command
    add_parser = subparsers.add_parser('add', help='Add new SSH profile')
    add_parser.add_argument('name', help='Profile name')
    add_parser.add_argument('host', help='SSH host')
    add_parser.add_argument('username', help='SSH username')
    add_parser.add_argument('-p', '--port', type=int, default=22, help='SSH port (default: 22)')
    add_parser.add_argument('-i', '--identity', help='Private key path')
    add_parser.add_argument('-j', '--jump', help='Jump host')
    add_parser.add_argument('-d', '--description', help='Profile description')

    # List profiles command
    subparsers.add_parser('list', help='List all SSH profiles')

    # Connect command
    connect_parser = subparsers.add_parser('connect', help='Connect to SSH profile')
    connect_parser.add_argument('name', help='Profile name to connect to')
    connect_parser.add_argument('--dry-run', action='store_true', help='Show command without executing')

    # Remove profile command
    remove_parser = subparsers.add_parser('remove', help='Remove SSH profile')
    remove_parser.add_argument('name', help='Profile name to remove')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search SSH profiles')
    search_parser.add_argument('query', help='Search query')

    # Stats command
    subparsers.add_parser('stats', help='Show profile statistics')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = SSHManager()

    if args.command == 'add':
        manager.add_profile(
            args.name, args.host, args.username, args.port,
            args.identity, args.jump, args.description
        )
    elif args.command == 'list':
        manager.list_profiles()
    elif args.command == 'connect':
        manager.connect(args.name, args.dry_run)
    elif args.command == 'remove':
        manager.remove_profile(args.name)
    elif args.command == 'search':
        manager.search_profiles(args.query)
    elif args.command == 'stats':
        manager.stats()

if __name__ == "__main__":
    main()
