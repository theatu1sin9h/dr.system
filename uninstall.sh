#!/usr/bin/env bash
# ==============================================================================
# Dr. System - Complete Uninstaller & Cleanup Tool
# Designed by - Atul Singh Chandel <myself.tas03@gmail.com>
# ==============================================================================

set -e

# ANSI Colors
RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
cat << "EOF"
 ____             ____            _                 
|  _ \ _ __      / ___| _   _ ___| |_ ___ _ __ ___  
| | | | '__|_____\___ \| | | / __| __/ _ \ '_ ` _ \ 
| |_| | | |_____| ___) | |_| \__ \ ||  __/ | | | | |
|____/|_|        |____/ \__, |___/\__\___|_| |_| |_|
                        |___/                       
EOF
echo -e "${NC}"
echo -e "${YELLOW}Designed by - Atul Singh Chandel <myself.tas03@gmail.com>${NC}"
echo -e "${BLUE}====================================================================${NC}"
echo -e "${RED}[!] WARNING: This will completely remove Dr. System from your computer.${NC}"
echo -e "Files to be removed:"
echo -e "  • Executable symlinks: ~/.local/bin/dr-system, ~/.local/bin/linux-doctor"
echo -e "  • Desktop shortcut:    ~/.local/share/applications/linux-doctor.desktop"
echo -e "  • Stored snapshots:    ~/.config/linux-doctor"
echo -e "  • Virtual environment: .venv/ (in repository directory)"
echo ""

# Confirm removal
read -p "Are you sure you want to proceed with full uninstallation? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}[*] Uninstallation aborted. No files were removed.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}[*] Removing symlinks from ~/.local/bin/...${NC}"
rm -f "$HOME/.local/bin/dr-system" 2>/dev/null || true
rm -f "$HOME/.local/bin/dr-system-gui" 2>/dev/null || true
rm -f "$HOME/.local/bin/linux-doctor" 2>/dev/null || true
rm -f "$HOME/.local/bin/linux-doctor-gui" 2>/dev/null || true

echo -e "${YELLOW}[*] Removing desktop menu entry...${NC}"
rm -f "$HOME/.local/share/applications/linux-doctor.desktop" 2>/dev/null || true

echo -e "${YELLOW}[*] Removing configuration and snapshots (~/.config/linux-doctor)...${NC}"
rm -rf "$HOME/.config/linux-doctor" 2>/dev/null || true

# Determine script root directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
if [ -d "$DIR/.venv" ]; then
    echo -e "${YELLOW}[*] Removing virtual environment ($DIR/.venv)...${NC}"
    rm -rf "$DIR/.venv" 2>/dev/null || true
fi

if [ -d "$DIR/build" ] || [ -d "$DIR/dist" ] || [ -d "$DIR/src/dr_system.egg-info" ] || [ -d "$DIR/src/linux_doctor.egg-info" ]; then
    echo -e "${YELLOW}[*] Cleaning build artifacts...${NC}"
    rm -rf "$DIR/build" "$DIR/dist" "$DIR"/src/*.egg-info 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}[✓] Dr. System has been completely uninstalled from your system.${NC}"
echo -e "${CYAN}To completely delete the repository folder, you can run:${NC}"
echo -e "  cd .. && rm -rf $DIR"
echo ""
