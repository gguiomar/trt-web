#!/bin/bash

echo "Starting server restart process..."

# Set up directories 
mkdir -p logs flask_session
chmod 775 logs flask_session

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

# Start Flask application in background
echo "Starting Flask application..."
python app.py > logs/flask.log 2>&1 &

echo "Server restart complete!"
echo "To check server status, use: ps aux | grep 'python app.py'"