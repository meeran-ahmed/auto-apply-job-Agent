#!/usr/bin/env bash
# OmniSwarm 1-Click Launcher for macOS & Linux

echo "======================================================================"
echo "            🚀 OMNISWARM: AI JOB APPLICATION ENGINE"
echo "                     Free & Open Source Edition"
echo "======================================================================"
echo ""

# Navigate to script directory
cd "$(dirname "$0")"

# Check virtual environment
if [ -f ".venv/bin/python" ]; then
    echo "[INFO] Starting OmniSwarm with virtual environment..."
    .venv/bin/python gui_main.py
    exit 0
fi

# Fallback to system python3
if command -v python3 &>/dev/null; then
    echo "[INFO] Starting OmniSwarm with system Python 3..."
    python3 gui_main.py
    exit 0
fi

echo "[ERROR] Python 3 was not found on your system."
echo "Please install Python 3.10+ to run OmniSwarm."
exit 1
