#!/bin/bash
set -e

echo "Deploying Music Curator Python Service..."

# Stop service if running
if systemctl is-active --quiet music-curator; then
    echo "Stopping existing service..."
    sudo systemctl stop music-curator
fi

# Copy systemd daemon configuration
echo "Copying systemd configuration..."
sudo cp systemd/music-curator.service /etc/systemd/system/

# Reload daemon and enable the service
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload
sudo systemctl enable music-curator

# Start the service
echo "Starting service..."
sudo systemctl start music-curator

echo "Deployment complete! Checking status:"
sudo systemctl status music-curator --no-pager
