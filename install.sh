#!/bin/bash

# SSH Profile Manager Installation Script
# Installs SSH Profile Manager for terminal use

set -e

echo "🚀 Installing SSH Profile Manager..."
echo "===================================="
echo

# Check Python availability
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is required but not installed."
    echo "Please install Python3 and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    echo "❌ Python 3.8+ is required, but you have Python $PYTHON_VERSION"
    echo "Please upgrade Python and try again."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create installation directory
INSTALL_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/ssh-manager"

echo "📂 Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$CONFIG_DIR/backups"

# Install GUI version
echo "🎨 Installing SSH Profile Manager GUI..."
cp ssh_gui.py "$INSTALL_DIR/ssh-gui"
chmod +x "$INSTALL_DIR/ssh-gui"

# Install CLI version
echo "⚡ Installing SSH Profile Manager CLI..."
cp ssh_manager.py "$INSTALL_DIR/ssh-manager"
chmod +x "$INSTALL_DIR/ssh-manager"

# Create convenient aliases
echo "🔗 Creating command aliases..."

# GUI aliases
if [ ! -f "$INSTALL_DIR/sshm" ]; then
    ln -sf "$INSTALL_DIR/ssh-gui" "$INSTALL_DIR/sshm"
    echo "   ✅ sshm -> ssh-gui"
fi

if [ ! -f "$INSTALL_DIR/ssh-profile-manager" ]; then
    ln -sf "$INSTALL_DIR/ssh-gui" "$INSTALL_DIR/ssh-profile-manager"
    echo "   ✅ ssh-profile-manager -> ssh-gui"
fi

# CLI aliases
if [ ! -f "$INSTALL_DIR/sshcli" ]; then
    ln -sf "$INSTALL_DIR/ssh-manager" "$INSTALL_DIR/sshcli"
    echo "   ✅ sshcli -> ssh-manager"
fi

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo
    echo "⚠️  Warning: $HOME/.local/bin is not in your PATH"
    echo "   Add this to your shell profile (~/.bashrc, ~/.zshrc, ~/.profile):"
    echo
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo
    echo "   Then restart your terminal or run: source ~/.bashrc"
    echo
fi

# Create sample configuration if it doesn't exist
if [ ! -f "$CONFIG_DIR/profiles.json" ]; then
    echo "📝 Creating sample configuration..."
    cat > "$CONFIG_DIR/profiles.json" << 'EOF'
{
  "version": "2.0",
  "profiles": [
    {
      "id": "example-prod",
      "name": "production-web",
      "host": "web.prod.example.com",
      "username": "deploy",
      "port": 22,
      "private_key_path": "~/.ssh/id_rsa_prod",
      "jump_host": null,
      "description": "Production web server",
      "tags": ["production", "web", "critical"],
      "created_at": "2025-01-20T10:00:00Z",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "example-dev",
      "name": "development-api",
      "host": "api.dev.example.com",
      "username": "developer",
      "port": 2222,
      "private_key_path": "~/.ssh/id_rsa_dev",
      "jump_host": null,
      "description": "Development API server",
      "tags": ["development", "api", "testing"],
      "created_at": "2025-01-20T10:00:00Z",
      "last_used": null,
      "use_count": 0
    },
    {
      "id": "example-db",
      "name": "database-server",
      "host": "db.internal.example.com",
      "username": "dbadmin",
      "port": 22,
      "private_key_path": "~/.ssh/id_rsa_db",
      "jump_host": "bastion@gateway.example.com",
      "description": "Database server (via bastion)",
      "tags": ["database", "production", "secure"],
      "created_at": "2025-01-20T10:00:00Z",
      "last_used": null,
      "use_count": 0
    }
  ]
}
EOF
    echo "   ✅ Sample profiles created"
fi

# Create desktop entry for Linux
if [ "$XDG_CURRENT_DESKTOP" ] && command -v desktop-file-install &> /dev/null; then
    echo "🖥️  Creating desktop entry..."
    DESKTOP_FILE="$HOME/.local/share/applications/ssh-profile-manager.desktop"
    mkdir -p "$(dirname "$DESKTOP_FILE")"

    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=SSH Profile Manager
Comment=Manage SSH connections with GUI interface
Exec=x-terminal-emulator -e $INSTALL_DIR/ssh-gui
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Network;System;Utility;
Keywords=ssh;terminal;connection;server;profile;
StartupNotify=true
EOF

    # Try to install it
    if command -v desktop-file-install &> /dev/null; then
        desktop-file-install --dir="$HOME/.local/share/applications" "$DESKTOP_FILE" 2>/dev/null || true
    fi
    echo "   ✅ Desktop entry created"
fi

# Create man page
echo "📖 Creating documentation..."
MAN_DIR="$HOME/.local/share/man/man1"
mkdir -p "$MAN_DIR"

cat > "$MAN_DIR/ssh-gui.1" << 'EOF'
.TH SSH-GUI 1 "January 2025" "SSH Profile Manager" "User Commands"
.SH NAME
ssh-gui \- SSH Profile Manager with GUI interface
.SH SYNOPSIS
.B ssh-gui
[\fI\,OPTION\/\fR]...
.SH DESCRIPTION
SSH Profile Manager is a powerful terminal-based SSH connection manager
with a beautiful GUI interface. It allows you to create, manage, and
organize SSH connection profiles with tags, statistics, and more.
.SH OPTIONS
.TP
\fB\-\-config\fR \fI\,CONFIG\/\fR
Custom config file path
.TP
\fB\-\-no\-color\fR
Disable colored output
.TP
\fB\-h\fR, \fB\-\-help\fR
Show help message and exit
.SH FILES
.TP
\fI\,~/.config/ssh-manager/profiles.json\/\fR
Main configuration file containing SSH profiles
.TP
\fI\,~/.config/ssh-manager/backups/\/\fR
Directory for automatic backups
.SH EXAMPLES
.TP
ssh-gui
Start the interactive GUI interface
.TP
ssh-gui --no-color
Start without colored output
.SH SEE ALSO
.BR ssh-manager (1),
.BR ssh (1),
.BR ssh-keygen (1)
EOF

cat > "$MAN_DIR/ssh-manager.1" << 'EOF'
.TH SSH-MANAGER 1 "January 2025" "SSH Profile Manager" "User Commands"
.SH NAME
ssh-manager \- SSH Profile Manager command line interface
.SH SYNOPSIS
.B ssh-manager
\fI\,COMMAND\/\fR [\fI\,ARGS\/\fR]...
.SH DESCRIPTION
Command line interface for SSH Profile Manager. Provides fast access
to SSH profile management operations.
.SH COMMANDS
.TP
\fBlist\fR
List all SSH profiles
.TP
\fBadd\fR \fI\,NAME HOST USERNAME\/\fR [\fI\,OPTIONS\/\fR]
Add new SSH profile
.TP
\fBconnect\fR \fI\,NAME\/\fR
Connect to SSH profile
.TP
\fBdelete\fR \fI\,NAME\/\fR
Delete SSH profile
.TP
\fBsearch\fR \fI\,QUERY\/\fR
Search SSH profiles
.TP
\fBstats\fR
Show profile statistics
.SH SEE ALSO
.BR ssh-gui (1),
.BR ssh (1)
EOF

echo "   ✅ Man pages created"

echo
echo "✅ Installation completed successfully!"
echo
echo "🎨 SSH Profile Manager Features:"
echo "   ✨ Beautiful terminal interface with colors"
echo "   📋 Interactive menus and navigation"
echo "   🔍 Advanced search with tags"
echo "   📊 Detailed statistics and usage tracking"
echo "   💾 Import/Export and backup functionality"
echo "   🎯 Quick connect with usage history"
echo "   🏷️  Profile tagging and organization"
echo
echo "🚀 Available Commands:"
echo "   ssh-gui                    # Interactive GUI interface"
echo "   sshm                       # Short alias for GUI"
echo "   ssh-profile-manager        # Full name alias"
echo "   ssh-manager                # Command line interface"
echo "   sshcli                     # Short alias for CLI"
echo
echo "📚 Quick Start:"
echo "   1. Run: ssh-gui"
echo "   2. Choose option 1 to see example profiles"
echo "   3. Choose option 2 to add your first profile"
echo "   4. Choose option 3 to connect to any server"
echo
echo "📂 Configuration: $CONFIG_DIR"
echo "📋 Executables:   $INSTALL_DIR"
echo

# Test installation
if command -v ssh-gui &> /dev/null; then
    echo "🧪 Testing installation..."
    echo "   ✅ ssh-gui command available"

    if command -v ssh-manager &> /dev/null; then
        echo "   ✅ ssh-manager command available"
    fi

    echo
    echo "🎉 Installation successful! Ready to use."
    echo
    echo "📖 Documentation:"
    echo "   man ssh-gui        # GUI manual"
    echo "   man ssh-manager    # CLI manual"
    echo "   ssh-gui --help     # Quick help"
    echo
    echo "🔧 First steps:"
    echo "   1. Run 'ssh-gui' to start the interface"
    echo "   2. Delete example profiles and add your own"
    echo "   3. Enjoy organized SSH management!"
else
    echo "⚠️  Installation may not be complete."
    echo "   PATH issue detected. Please add ~/.local/bin to your PATH:"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo
    echo "   Or run directly:"
    echo "   $INSTALL_DIR/ssh-gui"
fi

echo
echo "💡 Pro Tips:"
echo "   • Use tags to organize profiles: #production #database #web"
echo "   • Check statistics to see your most used connections"
echo "   • Create backups before major changes"
echo "   • Use CLI for automation: ssh-manager list | grep prod"
echo
echo "🌟 Star us on GitHub if you find this useful!"
echo "🐛 Report issues: GitHub Issues"
echo ""
echo "Made with 🐍 Python • 2025 • zeloras@gmail.com"
