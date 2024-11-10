# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the main.py file into the container
COPY . /app/

# Install common dependencies, these will be updated later
RUN apt-get update && \
    apt-get install -y git g++ && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
    
# Define the default command to keep the container running
CMD ["tail", "-f", "/dev/null"]
