FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy worker requirements
COPY worker/requirements.txt /app/worker/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r worker/requirements.txt

# Copy worker code
COPY worker/ /app/worker/

# Copy the root-level worker entrypoint
COPY worker.py /app/worker.py

# Copy src directory (all the heavy logic)
COPY src/ /app/src/

# Copy .env if exists
COPY .env* /app/

# Create vector_db directory
RUN mkdir -p /app/vector_db

# Run RQ worker for the 'learning-paths' queue
CMD ["python", "/app/worker.py"]
