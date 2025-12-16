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

# Create directories for TLS cert bind mounts
RUN mkdir -p /certs/ca /certs/game /certs/auth /certs/player


# Create non-root user for security
RUN addgroup --system --gid 1000 gameuser && \
    adduser --system --uid 1000 --gid 1000 --no-create-home gameuser && \
    chown -R gameuser:gameuser /app



# Switch to non-root user
USER gameuser

# Expose port
EXPOSE 8003

# Run the application (single-line JSON form to avoid parser issues)
CMD ["uvicorn","game_app.main:app","--host","0.0.0.0","--port","8003","--ssl-certfile","/certs/game/game.crt","--ssl-keyfile","/certs/game/game.key"]
