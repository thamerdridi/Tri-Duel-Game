# Base image: lightweight Python
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY game_app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY game_app /app/game_app

# Create non-root user for security
RUN addgroup --system --gid 1000 gameuser && \
    adduser --system --uid 1000 --gid 1000 --no-create-home gameuser && \
    chown -R gameuser:gameuser /app

# Switch to non-root user
USER gameuser

# Expose port
EXPOSE 8003

# Run the application
CMD ["uvicorn", "game_app.main:app", "--host", "0.0.0.0", "--port", "8003"]
