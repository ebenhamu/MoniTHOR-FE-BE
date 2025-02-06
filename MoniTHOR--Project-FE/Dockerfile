# Use the official Python image from the Docker Hub
FROM python

RUN mkdir /MoniTHOR--Project-FE  && chmod 777 /MoniTHOR--Project-FE 

# Copy application code to container
COPY . /MoniTHOR--Project-FE

# Set the working directory
WORKDIR /MoniTHOR--Project-FE

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt  --break-system-packages

# Set the default command to run the application
CMD ["python", "app.py"]
