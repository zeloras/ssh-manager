# SSH Profile Manager

A terminal SSH connection manager with GUI interface and advanced features.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
git clone <repository>
cd ssh-profile-manager
./install.sh
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

## 🤝 Contributing

Fork, make changes, submit PR. See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 📞 Support

- Issues: GitHub Issues
- Questions: GitHub Discussions

---

Made with 🐍 Python and vibe
