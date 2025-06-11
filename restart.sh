#!/bin/bash

echo "Starting VST application restart..."

# Set up directories 
mkdir -p logs flask_session
chmod 775 logs flask_session

# Activate conda environment with correct path
source /home/vst/miniconda3/etc/profile.d/conda.sh
conda activate vst

# Verify conda environment is activated
if [[ "$CONDA_DEFAULT_ENV" != "vst" ]]; then
    echo "✗ Failed to activate conda environment 'vst'"
    echo "Current environment: $CONDA_DEFAULT_ENV"
    exit 1
fi

echo "✓ Conda environment 'vst' activated successfully"
echo "Python path: $(which python)"
echo "Pip path: $(which pip)"

# Kill any running gunicorn processes
echo "Stopping any running gunicorn processes..."
pkill -f gunicorn || true
sleep 2

# Start single gunicorn application using conda environment's python
echo "Starting VST application..."
$(which gunicorn) app:app -b 0.0.0.0:5002 --workers 2 --timeout 60 --access-logfile logs/access.log --error-logfile logs/error.log > logs/gunicorn.log 2>&1 &

# Wait a moment for gunicorn to start
sleep 3

# Check if gunicorn is running
if pgrep -f gunicorn > /dev/null; then
    echo "✓ VST application started successfully"
    echo "Running processes:"
    ps aux | grep gunicorn | grep -v grep
    echo ""
    echo "🌐 Application accessible at: http://localhost:5002"
else
    echo "✗ Failed to start VST application"
    echo "Checking logs for errors..."
    tail -10 logs/error.log
    exit 1
fi

# Restart nginx
echo "Restarting nginx..."
sudo systemctl restart nginx

# Verify nginx is running
if systemctl is-active --quiet nginx; then
    echo "✓ Nginx restarted successfully"
else
    echo "✗ Failed to restart Nginx"
    exit 1
fi

echo ""
echo "🎉 VST application restart complete!"
echo ""
echo "📋 To check logs:"
echo "  tail -f logs/gunicorn.log"
echo "  tail -f logs/access.log"
echo "  tail -f logs/error.log"
echo "  tail -f flask_debug.log"
echo ""
echo "🔧 To stop application:"
echo "  pkill -f gunicorn"
