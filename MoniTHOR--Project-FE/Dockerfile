# Use the official Python image from the Docker Hub
FROM python

# Install dependencies for Chrome and Selenium
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add Google's official GPG key and set up the stable repository
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Install Google Chrome
RUN apt-get update && apt-get install -y --no-install-recommends google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install specific ChromeDriver version (replace with the correct version)
RUN wget -q https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip -O /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

# Create application directory
RUN mkdir /MoniTHOR--Project && chmod 777 /MoniTHOR--Project

# Copy application code to container
COPY . /MoniTHOR--Project

# Set the working directory
WORKDIR /MoniTHOR--Project

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the default command to run the application
CMD ["python", "app.py"]






# FROM python 
# RUN mkdir /systeminfo
# RUN chmod 777 /systeminfo
# COPY . /systeminfo
# WORKDIR /systeminfo
# RUN pip install -r requirements.txt
# CMD ["python", "app.py"]
