# Use Ubuntu as the base image
FROM ubuntu:latest

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update
# Update Ubuntu Software repository

# Install tzdata
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata

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
CMD [ "python3.11","-u","./DDNS-update.py" ]
