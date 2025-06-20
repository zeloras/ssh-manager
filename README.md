# SSH Profile Manager

A simple SSH connection manager for your terminal.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/yourusername/ssh-profile-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/ssh-profile-manager/actions/workflows/ci.yml)

## ✨ Features

- 🎨 **Beautiful GUI** - Interactive terminal interface with colors
- 📋 **Profile Management** - Create, edit, delete SSH profiles
- 🔍 **Search & Tags** - Find profiles with custom tags (#prod, #db)
- 📊 **Analytics** - Usage statistics and connection tracking
- 💾 **Import/Export** - Backup and restore configurations
- 🔐 **Security** - SSH keys and jump host support
- ⚡ **Fast** - Zero dependencies, instant startup

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository>
cd ssh-profile-manager

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt
```

### Usage

#### GUI Interface (Recommended)
```bash
ssh-gui          # Beautiful interactive interface
sshm             # Short alias
```

#### Command Line Interface
```bash
ssh-manager list                              # List all profiles
ssh-manager add myserver host.com user        # Add new profile
ssh-manager connect myserver                 # Connect to profile
ssh-manager search prod                      # Search profiles
ssh-manager delete myserver                 # Remove profile
```

## 🎮 Quick Demo

```
🚀 SSH Profile Manager
====================================
1. 📋 List profiles    2. ➕ Add profile
3. 🔌 Connect         4. ✏️  Edit profile
5. 🗑️  Delete         6. 🔍 Search
7. 📊 Statistics      0. Exit
```

## 🎯 Key Features
- Interactive terminal GUI with colors
- Profile tagging and organization
- Usage analytics and statistics
- SSH key and jump host support
- Import/export configurations
- Cross-platform compatibility

## 🔧 Configuration

Profiles stored in: `~/.config/ssh-manager/profiles.json`

## 🧪 Testing

```bash
# Make sure you're in your virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run all tests
pytest

# Run specific test types
pytest -m unit          # Unit tests
pytest -m integration   # Integration tests
pytest -m cli           # CLI tests

# Test with coverage
pytest --cov=ssh_manager --cov=ssh_gui --cov-report=term
```

## 🛠️ Code Quality

```bash
# Check code formatting
black --check ssh_manager.py ssh_gui.py tests/

# Apply code formatting
black ssh_manager.py ssh_gui.py tests/

# Run linter
flake8 ssh_manager.py ssh_gui.py tests/

# Type checking
mypy ssh_manager.py ssh_gui.py
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 📞 Support

- Issues: GitHub Issues
- Questions: GitHub Discussions

## 🛡️ Security

```bash
# Security audit
bandit -r ssh_manager.py ssh_gui.py

# Dependencies security check
safety check
```

---

Made with 🐍 Python and ❤️
