#!/bin/bash

# Change to script directory
cd "$(dirname "$0")"

# Create required directories
mkdir -p logs flask_session

# Kill any existing Flask instances
pkill -f "python app.py"

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate vst

# Start Flask in background with logging
nohup python app.py > logs/flask.log 2>&1 &

echo "Server started. Check logs/flask.log for details"