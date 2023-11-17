# Use Ubuntu as the base image
FROM ubuntu:latest

# Update Ubuntu Software repository
RUN apt-get update

# Install Python and pip
RUN apt-get install -y python3.11 python3-pip

# Upgrade pip
RUN python3.11 -m pip install --upgrade pip

# Install requests
RUN python3.11 -m pip install requests

# Set working directory in the container
WORKDIR /app

# Copy local code to the container
COPY . .

# Command to run on container start
CMD [ "python3.11", "./DDNS-update.py" ]