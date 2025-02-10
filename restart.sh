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

# Kill any running gunicorn processes
echo "Stopping any running gunicorn processes..."
pkill -f gunicorn || true
sleep 2

# Start gunicorn in background
echo "Starting gunicorn..."
gunicorn app:app -w 4 -b 127.0.0.1:5000 > logs/gunicorn.log 2>&1 &

# Restart nginx
echo "Restarting nginx..."
sudo systemctl restart nginx

echo "Server restart complete!"
echo "To check server status, use: ps aux | grep gunicorn"