# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for some Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
# This layer is cached, so it only rebuilds when requirements.txt changes
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Create necessary directories
RUN mkdir -p vector_db cache learning_paths

# Expose the port the app runs on (for the web service)
EXPOSE 5000

# Default command (this will be overridden by Render/Fly.io start commands)
# For web: gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
# For worker: python worker.py
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120"]
