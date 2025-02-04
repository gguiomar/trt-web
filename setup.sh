#!/bin/bash
echo "Setting up Conda environment for the Temporal Reasoning Task..."
echo "Creating conda environment..."
conda env create -f environment.yml
echo "Creating required directories..."
mkdir -p logs
mkdir -p static/css
mkdir -p static/js
echo "Setup complete! To activate the environment, run:"
echo "conda activate vst"
echo "Then start the application with: python app.py"