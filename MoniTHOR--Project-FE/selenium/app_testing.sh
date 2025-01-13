#!/bin/bash

# 

# Update and upgrade system
sudo apt update -y && sudo apt upgrade -y

# Install necessary packages
sudo apt install git python3-pip -y
sudo apt install chromium-browser
sudo apt install chromium-chromedriver

# Clone the project repository
git clone https://github.com/MayElbaz18/MoniTHOR--Project.git
cd MoniTHOR--Project/selenium

# Install Python dependencies
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt --break-system-packages --ignore-installed

# Set proper permissions
sudo chmod -R 777 .
