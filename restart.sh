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
chmod 755 logs

# Kill any running Flask processes
echo "Stopping any running Flask processes..."
pkill -f "python app.py" || true
sleep 2  # Wait for processes to stop

# Check and restart system services if they exist
if service_exists "flask.service"; then
    echo "Restarting Flask service..."
    sudo systemctl restart flask
fi

if command_exists "apache2"; then
    echo "Restarting Apache..."
    sudo systemctl restart apache2 || sudo service apache2 restart
fi

if command_exists "nginx"; then
    echo "Restarting Nginx..."
    sudo systemctl restart nginx || sudo service nginx restart
fi

# Activate conda environment if it exists
if command_exists "conda"; then
    echo "Activating conda environment..."
    source ~/miniconda3/etc/profile.d/conda.sh || source ~/anaconda3/etc/profile.d/conda.sh
    conda activate trt-web || echo "Warning: Could not activate conda environment"
fi

# Start Flask application
echo "Starting Flask application..."
python app.py &

echo "Server restart complete!"
echo "The game should now be accessible through your web browser."
echo "To check server status, use: ps aux | grep 'python app.py'"