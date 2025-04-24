# Dockerfile for DB Agent Flask application
# Created: Current date
# Author: Claude 3.7 Sonnet
# Description: Production-ready Docker image for the DB Agent application
# Updated: Fixed CMD format to use JSON array format

# Use Python 3.9 slim as base image for smaller size
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application with Gunicorn (using JSON array format)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT app:app"] 