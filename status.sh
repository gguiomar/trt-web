#!/bin/bash

echo "=== VST Server Status ==="
echo ""

# Check conda environment
echo "🐍 Conda Environment Status:"
source /home/vst/miniconda3/etc/profile.d/conda.sh
if conda env list | grep -q "^vst "; then
    echo "✓ Conda environment 'vst' exists"
    conda activate vst
    if [[ "$CONDA_DEFAULT_ENV" == "vst" ]]; then
        echo "✓ Conda environment 'vst' can be activated"
        echo "  Python: $(which python)"
        echo "  Gunicorn: $(which gunicorn 2>/dev/null || echo 'Not found')"
    else
        echo "✗ Failed to activate conda environment 'vst'"
    fi
else
    echo "✗ Conda environment 'vst' not found"
    echo "  Run './setup.sh' to create the environment"
fi

echo ""

# Check production servers
echo "🏭 Production Servers:"
if pgrep -f "gunicorn.*5000" > /dev/null; then
    echo "✓ Production server (port 5000) - RUNNING"
else
    echo "✗ Production server (port 5000) - STOPPED"
fi

if pgrep -f "gunicorn.*8000" > /dev/null; then
    echo "✓ Production server (port 8000) - RUNNING"
else
    echo "✗ Production server (port 8000) - STOPPED"
fi

echo ""

# Check development server
echo "🧪 Development Server:"
if pgrep -f "gunicorn.*5002" > /dev/null; then
    echo "✓ Development server (port 5002) - RUNNING"
    echo "  Process details:"
    ps aux | grep "gunicorn.*5002" | grep -v grep | head -3
else
    echo "✗ Development server (port 5002) - STOPPED"
fi

echo ""

# Show current git branch
echo "📋 Current Branch Information:"
cd /var/www/vst
echo "Current branch: $(git branch --show-current)"
echo "Last commit: $(git log -1 --oneline)"

echo ""

# Show access URLs
echo "🌐 Access URLs:"
echo "Production: http://127.0.0.1:5000 (v2)"
echo "Production: http://127.0.0.1:8000 (v2)"  
echo "Development (Local): http://127.0.0.1:5002 (v3.1)"
echo "Development (External): http://172.104.244.173:5002 (v3.1)"

echo ""

# Show recent log activity
echo "📊 Recent Development Log Activity:"
if [ -f logs/gunicorn-dev.log ]; then
    echo "Last 3 lines from development logs:"
    tail -n 3 logs/gunicorn-dev.log
else
    echo "No development logs found"
fi
