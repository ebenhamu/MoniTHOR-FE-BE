#!/bin/bash

# Update and upgrade system
sudo apt update -y && sudo apt upgrade -y

# Install necessary packages
sudo apt install git python3-pip -y

# Clone the project repository
git clone https://github.com/MayElbaz18/MoniTHOR--Project.git
sudo mv .env /home/ubuntu/MoniTHOR--Project
cd MoniTHOR--Project

# Install Python dependencies
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt --break-system-packages --ignore-installed

# Set proper permissions
sudo chmod -R 777 .

# Create a systemd service file for MoniTHOR
sudo bash -c 'cat << EOF > /etc/systemd/system/MoniTHOR.service
[Unit]
Description=MoniTHOR Flask application for domain monitoring
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/MoniTHOR--Project
EnvironmentFile=/home/ubuntu/MoniTHOR--Project/.env
ExecStart=/usr/bin/python3 /home/ubuntu/MoniTHOR--Project/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF'

# Reload systemd daemon to register the service
sudo systemctl daemon-reload

# Start and enable the MoniTHOR service
sudo systemctl start MoniTHOR.service
sudo systemctl enable MoniTHOR.service

# Stop UFW if necessary (consider configuring it properly instead of disabling)
sudo ufw disable

