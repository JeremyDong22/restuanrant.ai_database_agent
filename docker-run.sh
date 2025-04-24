#!/bin/bash
# docker-run.sh for DB Agent application
# Created: Current date
# Author: Claude 3.7 Sonnet
# Description: Script to build and run the Docker container
# Updated: Added check for SUPABASE_DB_URI environment variable

# Check if SUPABASE_DB_URI is set
if [ -z "${SUPABASE_DB_URI}" ]; then
  echo "⚠️  WARNING: SUPABASE_DB_URI environment variable is not set!"
  echo "The application will not function correctly without a valid database connection."
  echo "Please set this variable before running the container:"
  echo "export SUPABASE_DB_URI=\"postgresql://username:password@host:port/database\""
  
  read -p "Do you want to continue anyway? (y/n): " CONTINUE
  if [[ "$CONTINUE" != "y" && "$CONTINUE" != "Y" ]]; then
    echo "Exiting..."
    exit 1
  fi
  echo "Continuing without SUPABASE_DB_URI..."
fi

# Stop any existing container
echo "Stopping any existing dbagent container..."
docker stop dbagent 2>/dev/null || true
docker rm dbagent 2>/dev/null || true

# Build the Docker image
echo "Building dbagent Docker image..."
docker build -t dbagent .

# Set port (default: 8080 to avoid conflicts with common services)
PORT=${PORT:-8080}

# Run the container
echo "Running dbagent container on port $PORT..."
docker run -d \
  --name dbagent \
  -p $PORT:5000 \
  -e SUPABASE_DB_URI="${SUPABASE_DB_URI:-""}" \
  -e FLASK_ENV=${FLASK_ENV:-"development"} \
  dbagent

# Check if container is running
if [ "$(docker ps -q -f name=dbagent)" ]; then
  echo "✅ Container started! Access the application at http://localhost:$PORT"
  echo "To view logs: docker logs -f dbagent"
  echo "To stop: docker stop dbagent"
else
  echo "❌ Container failed to start. Check logs with: docker logs dbagent"
fi 