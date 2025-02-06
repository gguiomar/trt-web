#!/bin/bash

# Get the absolute path of the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Starting server restart process..."
echo "Script directory: $SCRIPT_DIR"

# Ensure correct working directory
cd "$SCRIPT_DIR" || exit 1

# Create PID file location
PID_FILE="$SCRIPT_DIR/flask.pid"

# Explicitly set up log directories with correct permissions
echo "Setting up log directories..."
mkdir -p logs flask_session
chmod 775 logs flask_session

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
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Stopping existing process ($OLD_PID)..."
        kill "$OLD_PID"
        sleep 2
    fi
    rm "$PID_FILE"
fi

# Start Flask application with log capture
echo "Starting Flask application..."
nohup python "$SCRIPT_DIR/app.py" > "$SCRIPT_DIR/logs/flask.log" 2>&1 & 
NEW_PID=$!

# Save the PID
echo $NEW_PID > "$PID_FILE"
echo "Flask started with PID: $NEW_PID"

# Verify the process is running
sleep 2
if kill -0 "$NEW_PID" 2>/dev/null; then
    echo "Server successfully started!"
    echo "Log file: $SCRIPT_DIR/logs/flask.log"
    echo "PID file: $PID_FILE"
else
    echo "Error: Server failed to start. Check logs for details."
    exit 1
fi

echo "To check server status, use: ps aux | grep 'python app.py'"
echo "To view logs, use: tail -f $SCRIPT_DIR/logs/flask.log"