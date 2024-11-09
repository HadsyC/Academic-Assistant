# Use the official Python image from Docker Hub
FROM python:3.11-slim

# Set environment variables to prevent .pyc files and enable stdout/stderr flushing
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose Django's default port
EXPOSE 8000
