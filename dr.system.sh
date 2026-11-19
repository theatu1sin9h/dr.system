#!/usr/bin/env bash
# ==============================================================================
# Dr. System - One-Click Launcher & Installer
# Designed by - Atul Singh Chandel <myself.tas03@gmail.com>
# ==============================================================================

set -e

# Detect Script Directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo -e "\033[1;36m"
cat << "EOF"
 ____             ____            _                 
|  _ \ _ __      / ___| _   _ ___| |_ ___ _ __ ___  
| | | | '__|_____\___ \| | | / __| __/ _ \ '_ ` _ \ 
| |_| | | |_____| ___) | |_| \__ \ ||  __/ | | | | |
|____/|_|        |____/ \__, |___/\__\___|_| |_| |_|
                        |___/                       
EOF
echo -e "\033[0m"
echo -e "\033[1;37mDesigned by - \033[1;33mAtul Singh Chandel \033[1;32m<myself.tas03@gmail.com>\033[0m"
echo -e "\033[1;34m====================================================================\033[0m"
echo -e "\033[1;32m[+] Checking Python 3 runtime...\033[0m"

# Find python3
if command -v python3 >/dev/null 2>&1; then
    PY_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PY_BIN="python"
else
    echo -e "\033[1;31m[-] Error: Python 3 is required but not installed.\033[0m"
    echo "Please install python3 using your distribution's package manager:"
    echo "  sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

# Ensure virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "\033[1;33m[*] Creating isolated virtual environment in .venv/...\033[0m"
    $PY_BIN -m venv .venv 2>/dev/null || {
        echo -e "\033[1;31m[-] python3-venv is missing. Installing standard packages...\033[0m"
        sudo apt-get update && sudo apt-get install -y python3-venv python3-pip || true
        $PY_BIN -m venv .venv
    }
fi

# Activate venv
source .venv/bin/activate

# Check if dependencies installed
if ! python -c "import psutil; import rich; import typer; import pydantic" >/dev/null 2>&1; then
    echo -e "\033[1;33m[*] First-time initialization: Installing Dr. System dependencies...\033[0m"
    pip install --upgrade pip >/dev/null 2>&1 || true
    pip install -e . >/dev/null 2>&1 || pip install -r requirements.txt
    echo -e "\033[1;32m[+] Dependencies successfully installed!\033[0m"
fi

# Link binary to ~/.local/bin if directory exists
mkdir -p "$HOME/.local/bin" 2>/dev/null || true
ln -sf "$DIR/.venv/bin/dr-system" "$HOME/.local/bin/dr-system" 2>/dev/null || true

echo -e "\033[1;32m[+] Launching Dr. System Master All-In-One Cyber Console...\033[0m"
sleep 1

# Launch Live All-In-One Terminal Console
exec python -c "from linux_doctor.cli.all_in_one_dashboard import run_all_in_one; run_all_in_one()" "$@"
