FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Backend/API code
COPY backend/ /app/backend/
COPY web_app/ /app/web_app/
COPY config.py /app/config.py
COPY init_render_db.py /app/init_render_db.py
COPY migrations/ /app/migrations/

# The backend imports application logic from src/
COPY src/ /app/src/

# Copy .env if exists
COPY .env* /app/

EXPOSE 5000

# Use shell form so $PORT expands when deployed
CMD ["sh", "-c", "gunicorn backend.app:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120"]