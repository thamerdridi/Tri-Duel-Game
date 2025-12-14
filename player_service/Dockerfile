FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (curl for health checks, openssl for self-signed TLS)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN addgroup --system app && adduser --system --ingroup app app

# Copy application code
COPY --chown=app:app app/ ./app/

# Entrypoint (TLS support)
COPY --chown=app:app entrypoint.sh /usr/local/bin/player_service_entrypoint.sh
RUN chmod +x /usr/local/bin/player_service_entrypoint.sh

# Expose port
EXPOSE 8002

# Drop privileges
USER app

# Run the application (optionally with TLS)
ENTRYPOINT ["/usr/local/bin/player_service_entrypoint.sh"]
