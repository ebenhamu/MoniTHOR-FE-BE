# Use the official Python image from the Docker Hub
FROM python

RUN mkdir /MoniTHOR--Project-BE  && chmod 777 /MoniTHOR--Project-BE

# Copy application code to container
COPY . /MoniTHOR--Project-BE

# Set the working directory
WORKDIR /MoniTHOR--Project-BE

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the default command to run the application
CMD ["python", "app.py"]