#!/bin/bash
# Simple wrapper script for resetting player data
# This ensures the correct Python interpreter is used

echo "VST Player Data Reset"
echo "===================="
echo ""

# Check if we're in the right directory
if [ ! -f "reset_player_data.py" ]; then
    echo "Error: reset_player_data.py not found in current directory"
    echo "Please run this script from the VST application root directory"
    exit 1
fi

# Use python3 to run the reset script
python3 reset_player_data.py "$@"
