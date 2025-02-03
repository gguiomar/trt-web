#!/bin/bash

echo "Starting server restart process..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a service exists
service_exists() {
    systemctl list-units --full -all | grep -Fq "$1"
}

# Create and set permissions for logs directory
echo "Setting up logs directory..."
mkdir -p logs
sudo chown -R $USER:$USER logs
sudo chmod -R 777 logs

# Stop any running Flask processes
echo "Stopping any running Flask processes..."
pkill -f "python app.py" || true
sleep 2

# Restart services
if service_exists "flask.service"; then
    echo "Restarting Flask service..."
    sudo systemctl restart flask
else
    echo "Flask service not found, running manually..."
    nohup python app.py > logs/flask.log 2>&1 &
fi

if command_exists "nginx"; then
    echo "Restarting Nginx..."
    sudo systemctl restart nginx || sudo service nginx restart
fi

# Activate conda environment
if command_exists "conda"; then
    echo "Activating conda environment..."
    source ~/miniconda3/etc/profile.d/conda.sh || source ~/anaconda3/etc/profile.d/conda.sh
    conda activate trt-web || echo "Warning: Could not activate conda environment"
fi

echo "Server restart complete!"
echo "To check logs: tail -f logs/flask.log"
