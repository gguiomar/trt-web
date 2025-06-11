#!/bin/bash
echo "Setting up Conda environment for the Temporal Reasoning Task..."

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "✗ Conda is not installed or not in PATH"
    echo "Please install Miniconda or Anaconda first"
    exit 1
fi

echo "Creating conda environment from environment.yml..."
conda env create -f environment.yml

# Check if environment was created successfully
if conda env list | grep -q "^vst "; then
    echo "✓ Conda environment 'vst' created successfully"
else
    echo "✗ Failed to create conda environment 'vst'"
    exit 1
fi

echo "Creating required directories..."
mkdir -p logs flask_session
mkdir -p static/css
mkdir -p static/js
chmod 775 logs flask_session

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 To activate the environment and start the application:"
echo "  conda activate vst"
echo "  python app.py"
echo ""
echo "🚀 Or use the restart script to run with gunicorn:"
echo "  ./restart.sh"
echo ""
echo "🔧 To stop the application:"
echo "  ./stop.sh"
