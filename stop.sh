#!/bin/bash

echo "Stopping VST application..."

# Activate conda environment for consistency
source /home/vst/miniconda3/etc/profile.d/conda.sh
conda activate vst

# Kill gunicorn processes
echo "Stopping gunicorn processes..."
pkill -f gunicorn || true

# Kill any direct Flask processes
echo "Stopping Flask processes..."
pkill -f "python app.py" || true

# Kill any conda environment python processes running the app
echo "Stopping any conda environment Flask processes..."
pkill -f "/home/vst/miniconda3/envs/vst/bin/python.*app.py" || true

# Wait for processes to stop
sleep 2

# Check if any processes are still running
if pgrep -f gunicorn > /dev/null; then
    echo "⚠️  Some gunicorn processes are still running"
    ps aux | grep gunicorn | grep -v grep
    echo ""
    echo "To force kill remaining processes, run:"
    echo "  pkill -9 -f gunicorn"
else
    echo "✓ All VST application processes stopped"
fi

echo ""
echo "🛑 VST application shutdown complete."
