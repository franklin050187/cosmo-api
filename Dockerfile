# Use official Python image as the base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Download the project source code from GitHub
ADD https://github.com/franklin050187/cosmo-api/archive/refs/heads/docker.zip /app

# Unzip the downloaded file
RUN unzip docker.zip && rm docker.zip && mv cosmo-api-docker cosmo-api

# Change the working directory to the project directory
WORKDIR /app/cosmo-api

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the .env file to the working directory
# load them in the container

# Expose port 8001
EXPOSE 8001

# Command to start the server
CMD ["python", "server.py"]
