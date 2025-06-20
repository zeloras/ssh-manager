#!/usr/bin/env python3
"""
SSH Profile Manager with GUI-like Terminal Interface
Enhanced version with interactive menus and visual interface
"""

import json
import os
import sys
import subprocess
import argparse
from datetime import datetime
from typing import Dict, List, Optional
import uuid

class Colors:
    """ANSI color codes for terminal styling"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    DIM = '\033[2m'

class SSHProfile:
    def __init__(self, name: str, host: str, username: str, port: int = 22,
                 private_key_path: str = None, jump_host: str = None,
                 description: str = None, tags: List[str] = None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.host = host
        self.username = username
        self.port = port
        self.private_key_path = private_key_path
        self.jump_host = jump_host
        self.description = description or f"SSH connection to {host}"
        self.tags = tags or []
        self.created_at = datetime.now().isoformat()
        self.last_used = None
        self.use_count = 0

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
            'tags': self.tags,
            'created_at': self.created_at,
            'last_used': self.last_used,
            'use_count': self.use_count
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
            description=data.get('description'),
            tags=data.get('tags', [])
        )
        profile.id = data['id']
        profile.created_at = data.get('created_at', datetime.now().isoformat())
        profile.last_used = data.get('last_used')
        profile.use_count = data.get('use_count', 0)
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

class SSHManagerGUI:
    def __init__(self, config_file: str = None):
        if config_file is None:
            config_dir = os.path.expanduser("~/.config/ssh-manager")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "profiles.json")

        self.config_file = config_file
        self.profiles: Dict[str, SSHProfile] = {}
        self.load_profiles()

    def clear_screen(self):
        """Clear terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')

    def print_header(self, title: str):
        """Print styled header"""
        width = 80
        print(f"\n{Colors.CYAN}{'=' * width}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{title.center(width)}{Colors.END}")
        print(f"{Colors.CYAN}{'=' * width}{Colors.END}\n")

    def print_box(self, content: str, color: str = Colors.BLUE):
        """Print content in a box"""
        lines = content.split('\n')
        max_width = max(len(line) for line in lines) + 4

        print(f"{color}┌{'─' * (max_width - 2)}┐{Colors.END}")
        for line in lines:
            padding = max_width - len(line) - 4
            print(f"{color}│ {line}{' ' * padding} │{Colors.END}")
        print(f"{color}└{'─' * (max_width - 2)}┘{Colors.END}")

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
                print(f"{Colors.RED}Error loading profiles: {e}{Colors.END}")

    def save_profiles(self):
        """Save profiles to config file"""
        data = {
            'version': '2.0',
            'profiles': [profile.to_dict() for profile in self.profiles.values()]
        }

        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)

    def show_main_menu(self):
        """Display main menu"""
        while True:
            self.clear_screen()
            self.print_header("🚀 SSH Profile Manager")

            print(f"{Colors.BOLD}Select an option:{Colors.END}\n")
            print(f"{Colors.GREEN}1.{Colors.END} 📋 List all profiles")
            print(f"{Colors.GREEN}2.{Colors.END} ➕ Add new profile")
            print(f"{Colors.GREEN}3.{Colors.END} 🔌 Connect to profile")
            print(f"{Colors.GREEN}4.{Colors.END} ✏️  Edit profile")
            print(f"{Colors.GREEN}5.{Colors.END} 🗑️  Delete profile")
            print(f"{Colors.GREEN}6.{Colors.END} 🔍 Search profiles")
            print(f"{Colors.GREEN}7.{Colors.END} 📊 View statistics")
            print(f"{Colors.GREEN}8.{Colors.END} 📁 Import/Export")
            print(f"{Colors.GREEN}9.{Colors.END} ⚙️  Settings")
            print(f"{Colors.RED}0.{Colors.END} 🚪 Exit")

            print(f"\n{Colors.YELLOW}Total profiles: {len(self.profiles)}{Colors.END}")

            choice = input(f"\n{Colors.BOLD}Enter your choice (0-9): {Colors.END}")

            if choice == '1':
                self.show_profiles_list()
            elif choice == '2':
                self.add_profile_interactive()
            elif choice == '3':
                self.connect_interactive()
            elif choice == '4':
                self.edit_profile_interactive()
            elif choice == '5':
                self.delete_profile_interactive()
            elif choice == '6':
                self.search_interactive()
            elif choice == '7':
                self.show_statistics()
            elif choice == '8':
                self.import_export_menu()
            elif choice == '9':
                self.settings_menu()
            elif choice == '0':
                print(f"\n{Colors.GREEN}👋 Goodbye!{Colors.END}")
                sys.exit(0)
            else:
                print(f"\n{Colors.RED}❌ Invalid choice. Please try again.{Colors.END}")
                input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")

    def show_profiles_list(self):
        """Display profiles in a formatted list"""
        self.clear_screen()
        self.print_header("📋 SSH Profiles")

        if not self.profiles:
            self.print_box("No profiles configured yet.\nUse 'Add new profile' to create your first one.", Colors.YELLOW)
            input(f"\n{Colors.DIM}Press Enter to continue...{Colors.END}")
            return

        profiles = sorted(self.profiles.values(), key=lambda p: p.last_used or "0", reverse=True)

        for i, profile in enumerate(profiles, 1):
            status_icon = "🟢" if profile.last_used else "⚪"
            tags_str = " ".join([f"#{tag}" for tag in profile.tags]) if profile.tags else ""

            print(f"{Colors.BOLD}{i:2d}. {status_icon} {profile.name}{Colors.END}")
            print(f"    {Colors.BLUE}Host:{Colors.END} {profile.username}@{profile.host}:{profile.port}")
            if profile.private_key_path:
                print(f"    {Colors.BLUE}Key:{Colors.END} {profile.private_key_path}")
            if profile.jump_host:
                print(f"    {Colors.BLUE}Jump:{Colors.END} {profile.jump_host}")
            if profile.description:
                print(f"    {Colors.DIM}{profile.description}{Colors.END}")
            if tags_str:
                print(f"    {Colors.CYAN}{tags_str}{Colors.END}")
            if profile.use_count > 0:
                print(f"    {Colors.DIM}Used {profile.use_count} times{Colors.END}")
            print()

        choice = input(f"{Colors.BOLD}Enter profile number to connect, or press Enter to return: {Colors.END}")
        if choice.isdigit() and 1 <= int(choice) <= len(profiles):
            profile = profiles[int(choice) - 1]
            self.connect_to_profile(profile)

    def add_profile_interactive(self):
        """Interactive profile creation"""
        self.clear_screen()
        self.print_header("➕ Add New SSH Profile")

        try:
            name = input(f"{Colors.BOLD}Profile name: {Colors.END}").strip()
            if not name:
                print(f"{Colors.RED}❌ Profile name cannot be empty{Colors.END}")
                input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")
                return

            if name in self.profiles:
                print(f"{Colors.RED}❌ Profile '{name}' already exists{Colors.END}")
                input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")
                return

            host = input(f"{Colors.BOLD}Host/IP address: {Colors.END}").strip()
            if not host:
                print(f"{Colors.RED}❌ Host cannot be empty{Colors.END}")
                input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")
                return

            username = input(f"{Colors.BOLD}Username: {Colors.END}").strip()
            if not username:
                print(f"{Colors.RED}❌ Username cannot be empty{Colors.END}")
                input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")
                return

            port_str = input(f"{Colors.BOLD}Port (default 22): {Colors.END}").strip()
            port = 22
            if port_str:
                try:
                    port = int(port_str)
                    if port <= 0 or port > 65535:
                        raise ValueError
                except ValueError:
                    print(f"{Colors.RED}❌ Invalid port number{Colors.END}")
                    input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")
                    return

            private_key = input(f"{Colors.BOLD}Private key path (optional): {Colors.END}").strip()
            if private_key and not os.path.exists(os.path.expanduser(private_key)):
                confirm = input(f"{Colors.YELLOW}⚠️  Key file doesn't exist. Continue? (y/N): {Colors.END}")
                if confirm.lower() != 'y':
                    return

            jump_host = input(f"{Colors.BOLD}Jump host (optional): {Colors.END}").strip()
            description = input(f"{Colors.BOLD}Description (optional): {Colors.END}").strip()
            tags_str = input(f"{Colors.BOLD}Tags (space-separated, optional): {Colors.END}").strip()
            tags = tags_str.split() if tags_str else []

            profile = SSHProfile(
                name=name,
                host=host,
                username=username,
                port=port,
                private_key_path=private_key if private_key else None,
                jump_host=jump_host if jump_host else None,
                description=description if description else None,
                tags=tags
            )

            self.profiles[name] = profile
            self.save_profiles()

            print(f"\n{Colors.GREEN}✅ Profile '{name}' created successfully!{Colors.END}")

            connect_now = input(f"{Colors.BOLD}Connect now? (y/N): {Colors.END}")
            if connect_now.lower() == 'y':
                self.connect_to_profile(profile)

        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}❌ Cancelled{Colors.END}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")

    def connect_interactive(self):
        """Interactive connection selection"""
        if not self.profiles:
            self.clear_screen()
            self.print_box("No profiles available.\nCreate a profile first.", Colors.YELLOW)
            input(f"\n{Colors.DIM}Press Enter to continue...{Colors.END}")
            return

        self.clear_screen()
        self.print_header("🔌 Connect to SSH Profile")

        profiles = list(self.profiles.values())
        for i, profile in enumerate(profiles, 1):
            status = f"(used {profile.use_count} times)" if profile.use_count > 0 else "(never used)"
            print(f"{Colors.GREEN}{i:2d}.{Colors.END} {profile.name} - {profile.username}@{profile.host} {Colors.DIM}{status}{Colors.END}")

        choice = input(f"\n{Colors.BOLD}Select profile (1-{len(profiles)}): {Colors.END}")

        try:
            index = int(choice) - 1
            if 0 <= index < len(profiles):
                self.connect_to_profile(profiles[index])
            else:
                print(f"{Colors.RED}❌ Invalid selection{Colors.END}")
                input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")
        except ValueError:
            print(f"{Colors.RED}❌ Invalid input{Colors.END}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")

    def connect_to_profile(self, profile: SSHProfile):
        """Connect to SSH profile"""
        ssh_cmd = profile.generate_ssh_command()

        self.clear_screen()
        self.print_header(f"🚀 Connecting to {profile.name}")

        print(f"{Colors.BOLD}Profile:{Colors.END} {profile.name}")
        print(f"{Colors.BOLD}Host:{Colors.END} {profile.username}@{profile.host}:{profile.port}")
        if profile.description:
            print(f"{Colors.BOLD}Description:{Colors.END} {profile.description}")
        print(f"\n{Colors.BOLD}SSH Command:{Colors.END}")
        self.print_box(ssh_cmd, Colors.GREEN)

        choice = input(f"\n{Colors.BOLD}[C]onnect, [S]how command only, or [R]eturn: {Colors.END}").lower()

        if choice == 'c':
            print(f"\n{Colors.GREEN}🔌 Connecting...{Colors.END}")

            # Update usage statistics
            profile.last_used = datetime.now().isoformat()
            profile.use_count += 1
            self.save_profiles()

            try:
                subprocess.run(ssh_cmd.split())
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}👋 Connection interrupted{Colors.END}")
            except Exception as e:
                print(f"\n{Colors.RED}❌ Connection failed: {e}{Colors.END}")

            input(f"\n{Colors.DIM}Press Enter to continue...{Colors.END}")
        elif choice == 's':
            print(f"\n{Colors.CYAN}📋 Command copied to clipboard (if available){Colors.END}")
            try:
                subprocess.run(['pbcopy'], input=ssh_cmd.encode(), check=True)
            except:
                pass
            input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")

    def edit_profile_interactive(self):
        """Interactive profile editing"""
        if not self.profiles:
            self.clear_screen()
            self.print_box("No profiles to edit.", Colors.YELLOW)
            input(f"\n{Colors.DIM}Press Enter to continue...{Colors.END}")
            return

        # Show profiles and let user select
        self.clear_screen()
        self.print_header("✏️ Edit Profile")

        profiles = list(self.profiles.values())
        for i, profile in enumerate(profiles, 1):
            print(f"{Colors.GREEN}{i:2d}.{Colors.END} {profile.name}")

        choice = input(f"\n{Colors.BOLD}Select profile to edit (1-{len(profiles)}): {Colors.END}")

        try:
            index = int(choice) - 1
            if 0 <= index < len(profiles):
                profile = profiles[index]

                print(f"\n{Colors.BOLD}Editing: {profile.name}{Colors.END}")
                print(f"{Colors.DIM}Press Enter to keep current value{Colors.END}\n")

                # Edit fields
                new_name = input(f"Name [{profile.name}]: ").strip()
                if new_name and new_name != profile.name:
                    if new_name in self.profiles:
                        print(f"{Colors.RED}❌ Name already exists{Colors.END}")
                        input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")
                        return
                    del self.profiles[profile.name]
                    profile.name = new_name

                new_host = input(f"Host [{profile.host}]: ").strip()
                if new_host:
                    profile.host = new_host

                new_username = input(f"Username [{profile.username}]: ").strip()
                if new_username:
                    profile.username = new_username

                new_port = input(f"Port [{profile.port}]: ").strip()
                if new_port:
                    try:
                        profile.port = int(new_port)
                    except ValueError:
                        print(f"{Colors.RED}❌ Invalid port{Colors.END}")

                new_key = input(f"Private key [{profile.private_key_path or 'None'}]: ").strip()
                if new_key:
                    profile.private_key_path = new_key

                new_jump = input(f"Jump host [{profile.jump_host or 'None'}]: ").strip()
                if new_jump:
                    profile.jump_host = new_jump

                new_desc = input(f"Description [{profile.description}]: ").strip()
                if new_desc:
                    profile.description = new_desc

                self.profiles[profile.name] = profile
                self.save_profiles()

                print(f"\n{Colors.GREEN}✅ Profile updated successfully!{Colors.END}")
                input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")
            else:
                print(f"{Colors.RED}❌ Invalid selection{Colors.END}")
                input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")
        except ValueError:
            print(f"{Colors.RED}❌ Invalid input{Colors.END}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")

    def delete_profile_interactive(self):
        """Interactive profile deletion"""
        if not self.profiles:
            self.clear_screen()
            self.print_box("No profiles to delete.", Colors.YELLOW)
            input(f"\n{Colors.DIM}Press Enter to continue...{Colors.END}")
            return

        self.clear_screen()
        self.print_header("🗑️ Delete Profile")

        profiles = list(self.profiles.values())
        for i, profile in enumerate(profiles, 1):
            print(f"{Colors.RED}{i:2d}.{Colors.END} {profile.name}")

        choice = input(f"\n{Colors.BOLD}Select profile to delete (1-{len(profiles)}): {Colors.END}")

        try:
            index = int(choice) - 1
            if 0 <= index < len(profiles):
                profile = profiles[index]

                confirm = input(f"{Colors.RED}❗ Delete '{profile.name}'? This cannot be undone! (yes/no): {Colors.END}")
                if confirm.lower() == 'yes':
                    del self.profiles[profile.name]
                    self.save_profiles()
                    print(f"\n{Colors.GREEN}✅ Profile '{profile.name}' deleted{Colors.END}")
                else:
                    print(f"\n{Colors.YELLOW}❌ Cancelled{Colors.END}")

                input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")
            else:
                print(f"{Colors.RED}❌ Invalid selection{Colors.END}")
                input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")
        except ValueError:
            print(f"{Colors.RED}❌ Invalid input{Colors.END}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")

    def search_interactive(self):
        """Interactive profile search"""
        self.clear_screen()
        self.print_header("🔍 Search Profiles")

        query = input(f"{Colors.BOLD}Enter search query: {Colors.END}").strip()
        if not query:
            return

        results = []
        query_lower = query.lower()

        for profile in self.profiles.values():
            if (query_lower in profile.name.lower() or
                query_lower in profile.host.lower() or
                query_lower in profile.username.lower() or
                query_lower in profile.description.lower() or
                any(query_lower in tag.lower() for tag in profile.tags)):
                results.append(profile)

        if not results:
            print(f"\n{Colors.YELLOW}📭 No profiles found matching '{query}'{Colors.END}")
        else:
            print(f"\n{Colors.GREEN}📋 Found {len(results)} profile(s):{Colors.END}\n")
            for i, profile in enumerate(results, 1):
                print(f"{Colors.GREEN}{i:2d}.{Colors.END} {profile.name} - {profile.username}@{profile.host}")

            choice = input(f"\n{Colors.BOLD}Select profile to connect (1-{len(results)}) or Enter to return: {Colors.END}")
            if choice.isdigit() and 1 <= int(choice) <= len(results):
                self.connect_to_profile(results[int(choice) - 1])

        input(f"\n{Colors.DIM}Press Enter to continue...{Colors.END}")

    def show_statistics(self):
        """Display detailed statistics"""
        self.clear_screen()
        self.print_header("📊 SSH Profile Statistics")

        if not self.profiles:
            self.print_box("No profiles to analyze.", Colors.YELLOW)
            input(f"\n{Colors.DIM}Press Enter to continue...{Colors.END}")
            return

        total = len(self.profiles)
        with_keys = sum(1 for p in self.profiles.values() if p.private_key_path)
        with_jump = sum(1 for p in self.profiles.values() if p.jump_host)
        never_used = sum(1 for p in self.profiles.values() if p.use_count == 0)

        # Port statistics
        ports = {}
        for profile in self.profiles.values():
            ports[profile.port] = ports.get(profile.port, 0) + 1

        # Most used profiles
        most_used = sorted(self.profiles.values(), key=lambda p: p.use_count, reverse=True)[:5]

        print(f"{Colors.BOLD}📈 General Statistics:{Colors.END}")
        print(f"   • Total profiles: {Colors.CYAN}{total}{Colors.END}")
        print(f"   • With SSH keys: {Colors.GREEN}{with_keys}{Colors.END}")
        print(f"   • With jump hosts: {Colors.BLUE}{with_jump}{Colors.END}")
        print(f"   • Never used: {Colors.YELLOW}{never_used}{Colors.END}")

        print(f"\n{Colors.BOLD}🔌 Port Distribution:{Colors.END}")
        for port, count in sorted(ports.items()):
            bar = "█" * min(20, count * 20 // max(ports.values()) if ports.values() else 0)
            print(f"   Port {port:5d}: {Colors.CYAN}{bar}{Colors.END} {count}")

        if any(p.use_count > 0 for p in most_used):
            print(f"\n{Colors.BOLD}🏆 Most Used Profiles:{Colors.END}")
            for i, profile in enumerate(most_used[:5], 1):
                if profile.use_count > 0:
                    print(f"   {i}. {profile.name}: {Colors.GREEN}{profile.use_count} times{Colors.END}")

        input(f"\n{Colors.DIM}Press Enter to continue...{Colors.END}")

    def import_export_menu(self):
        """Import/Export menu"""
        self.clear_screen()
        self.print_header("📁 Import/Export Profiles")

        print(f"{Colors.BOLD}Select an option:{Colors.END}\n")
        print(f"{Colors.GREEN}1.{Colors.END} 📤 Export profiles to file")
        print(f"{Colors.GREEN}2.{Colors.END} 📥 Import profiles from file")
        print(f"{Colors.GREEN}3.{Colors.END} 🔄 Backup current profiles")
        print(f"{Colors.RED}0.{Colors.END} ↩️  Return to main menu")

        choice = input(f"\n{Colors.BOLD}Enter your choice: {Colors.END}")

        if choice == '1':
            self.export_profiles()
        elif choice == '2':
            self.import_profiles()
        elif choice == '3':
            self.backup_profiles()

    def export_profiles(self):
        """Export profiles to file"""
        filename = input(f"{Colors.BOLD}Export filename (default: ssh-profiles-backup.json): {Colors.END}").strip()
        if not filename:
            filename = "ssh-profiles-backup.json"

        try:
            data = {
                'version': '2.0',
                'exported_at': datetime.now().isoformat(),
                'profiles': [profile.to_dict() for profile in self.profiles.values()]
            }

            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"\n{Colors.GREEN}✅ Exported {len(self.profiles)} profiles to {filename}{Colors.END}")
        except Exception as e:
            print(f"\n{Colors.RED}❌ Export failed: {e}{Colors.END}")

        input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")

    def import_profiles(self):
        """Import profiles from file"""
        filename = input(f"{Colors.BOLD}Import filename: {Colors.END}").strip()
        if not filename or not os.path.exists(filename):
            print(f"{Colors.RED}❌ File not found{Colors.END}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")
            return

        try:
            with open(filename, 'r') as f:
                data = json.load(f)

            imported_profiles = []
            for profile_data in data.get('profiles', []):
                profile = SSHProfile.from_dict(profile_data)
                if profile.name in self.profiles:
                    overwrite = input(f"{Colors.YELLOW}Profile '{profile.name}' exists. Overwrite? (y/N): {Colors.END}")
                    if overwrite.lower() != 'y':
                        continue

                self.profiles[profile.name] = profile
                imported_profiles.append(profile.name)

            self.save_profiles()
            print(f"\n{Colors.GREEN}✅ Imported {len(imported_profiles)} profiles{Colors.END}")

        except Exception as e:
            print(f"\n{Colors.RED}❌ Import failed: {e}{Colors.END}")

        input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")

    def backup_profiles(self):
        """Create automatic backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.expanduser("~/.config/ssh-manager/backups")
        os.makedirs(backup_dir, exist_ok=True)

        backup_file = os.path.join(backup_dir, f"profiles_backup_{timestamp}.json")

        try:
            data = {
                'version': '2.0',
                'backup_created_at': datetime.now().isoformat(),
                'profiles': [profile.to_dict() for profile in self.profiles.values()]
            }

            with open(backup_file, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"\n{Colors.GREEN}✅ Backup created: {backup_file}{Colors.END}")
        except Exception as e:
            print(f"\n{Colors.RED}❌ Backup failed: {e}{Colors.END}")

        input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")

    def settings_menu(self):
        """Settings menu"""
        self.clear_screen()
        self.print_header("⚙️ Settings")

        print(f"{Colors.BOLD}Configuration:{Colors.END}")
        print(f"   • Config file: {Colors.CYAN}{self.config_file}{Colors.END}")
        print(f"   • Profiles: {Colors.GREEN}{len(self.profiles)}{Colors.END}")

        print(f"\n{Colors.BOLD}Options:{Colors.END}")
        print(f"{Colors.GREEN}1.{Colors.END} 🔄 Reset all profiles")
        print(f"{Colors.GREEN}2.{Colors.END} 📂 Open config directory")
        print(f"{Colors.GREEN}3.{Colors.END} 🧹 Clean unused backups")
        print(f"{Colors.RED}0.{Colors.END} ↩️  Return to main menu")

        choice = input(f"\n{Colors.BOLD}Enter your choice: {Colors.END}")

        if choice == '1':
            self.reset_profiles()
        elif choice == '2':
            self.open_config_directory()
        elif choice == '3':
            self.clean_backups()

    def reset_profiles(self):
        """Reset all profiles after confirmation"""
        confirm = input(f"{Colors.RED}❗ Delete ALL profiles? This cannot be undone! Type 'DELETE ALL' to confirm: {Colors.END}")
        if confirm == 'DELETE ALL':
            self.profiles.clear()
            self.save_profiles()
            print(f"\n{Colors.GREEN}✅ All profiles deleted{Colors.END}")
        else:
            print(f"\n{Colors.YELLOW}❌ Cancelled{Colors.END}")

        input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")

    def open_config_directory(self):
        """Open config directory in file manager"""
        config_dir = os.path.dirname(self.config_file)
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", config_dir])
            elif sys.platform == "linux":  # Linux
                subprocess.run(["xdg-open", config_dir])
            elif sys.platform == "win32":  # Windows
                subprocess.run(["explorer", config_dir])
            print(f"\n{Colors.GREEN}✅ Opened config directory{Colors.END}")
        except Exception as e:
            print(f"\n{Colors.RED}❌ Failed to open directory: {e}{Colors.END}")

        input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")

    def clean_backups(self):
        """Clean old backup files"""
        backup_dir = os.path.expanduser("~/.config/ssh-manager/backups")
        if not os.path.exists(backup_dir):
            print(f"\n{Colors.YELLOW}📭 No backups found{Colors.END}")
            input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")
            return

        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
        if len(backup_files) <= 5:
            print(f"\n{Colors.GREEN}✅ Only {len(backup_files)} backups found, no cleanup needed{Colors.END}")
        else:
            # Keep only latest 5 backups
            backup_files.sort(reverse=True)
            files_to_delete = backup_files[5:]

            for file in files_to_delete:
                os.remove(os.path.join(backup_dir, file))

            print(f"\n{Colors.GREEN}✅ Cleaned up {len(files_to_delete)} old backups{Colors.END}")

        input(f"{Colors.DIM}Press Enter to continue...{Colors.END}")

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="SSH Profile Manager with GUI-like Terminal Interface")
    parser.add_argument('--config', help='Custom config file path')
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')

    args = parser.parse_args()

    # Disable colors if requested
    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')

    try:
        manager = SSHManagerGUI(args.config)
        manager.show_main_menu()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}👋 Goodbye!{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Fatal error: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()
