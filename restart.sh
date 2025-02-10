#!/bin/bash

echo "Starting server restart process..."

# Set up directories 
mkdir -p logs flask_session
chmod 775 logs flask_session

# Activate conda environment with correct path
source /home/vst/miniconda3/etc/profile.d/conda.sh
conda activate vst

# Kill any running gunicorn processes
echo "Stopping any running gunicorn processes..."
pkill -f gunicorn || true
sleep 2

# Start gunicorn in background
echo "Starting gunicorn..."
gunicorn app:app -b 127.0.0.1:5000 --access-logfile logs/access.log --error-logfile logs/error.log > logs/gunicorn.log 2>&1 &

# Wait a moment for gunicorn to start
sleep 2

# Check if gunicorn is running
if pgrep -f gunicorn > /dev/null; then
    echo "✓ Gunicorn started successfully"
    echo "Gunicorn processes:"
    ps aux | grep gunicorn | grep -v grep
else
    echo "✗ Failed to start Gunicorn"
    exit 1
fi

# Restart nginx
echo "Restarting nginx..."
sudo systemctl restart nginx

# Verify nginx is running
if systemctl is-active --quiet nginx; then
    echo "✓ Nginx restarted successfully"
    echo "Nginx status:"
    systemctl status nginx | head -n 3
else
    echo "✗ Failed to restart Nginx"
    exit 1
fi

echo "Server restart complete!"
echo "To check logs:"
echo "tail -f logs/gunicorn.log"
echo "tail -f /var/log/nginx/error.log"