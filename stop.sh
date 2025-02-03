#!/bin/bash

echo "Stopping all server processes..."

# Kill Flask processes
echo "Stopping Flask processes..."
pkill -f "python app.py" || true

# Function to check if a service exists
service_exists() {
    systemctl list-units --full -all | grep -Fq "$1"
}

# Stop system services if they exist
if service_exists "flask.service"; then
    echo "Stopping Flask service..."
    sudo systemctl stop flask
fi

if service_exists "apache2.service"; then
    echo "Stopping Apache..."
    sudo systemctl stop apache2 || sudo service apache2 stop
fi

if service_exists "nginx.service"; then
    echo "Stopping Nginx..."
    sudo systemctl stop nginx || sudo service nginx stop
fi

echo "All server processes have been stopped."