#!/bin/bash

# Get the absolute path of the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Starting server restart process..."
echo "Script directory: $SCRIPT_DIR"

# Ensure correct working directory
cd "$SCRIPT_DIR" || exit 1

# Explicitly set up log directories with correct permissions
echo "Setting up log directories..."
mkdir -p logs flask_session
chmod 775 logs flask_session

# Ensure correct ownership (replace 'your_user' with the actual user)
# Uncomment and modify if needed
# sudo chown your_user:your_group logs flask_session

# Detailed logging of directory setup
echo "Log directory details:"
ls -ld logs flask_session

# Activate conda environment (if used)
if command -v conda &> /dev/null; then
    echo "Activating conda environment..."
    source ~/miniconda3/etc/profile.d/conda.sh || source ~/anaconda3/etc/profile.d/conda.sh
    conda activate vst || echo "Warning: Could not activate conda environment"
fi

# Kill any running Flask processes
echo "Stopping any running Flask processes..."
pkill -f "python app.py" || true
sleep 2

# Start Flask application with full path and verbose output
echo "Starting Flask application..."
python "app.py" &

# Optional: Run diagnostic script to verify logging
python "$/utils/logging_diagnostic.py"

echo "Server restart complete!"
echo "To check server status, use: ps aux | grep 'python app.py'"