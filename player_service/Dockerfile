FROM python:3.12-slim

WORKDIR /app

# ------------------------------------------------------------
# System dependencies (curl for healthcheck, openssl for TLS)
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# ------------------------------------------------------------
# Python dependencies
# ------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ------------------------------------------------------------
# Create non-root user
# ------------------------------------------------------------
RUN addgroup --system app && adduser --system --ingroup app app

# ------------------------------------------------------------
# Application code
# ------------------------------------------------------------
COPY --chown=app:app app/ ./app/

# ------------------------------------------------------------
# Prepare directories for TLS cert bind mounts
# (must exist before Docker mounts volumes)
# ------------------------------------------------------------
RUN mkdir -p /certs/ca /certs/player

# ------------------------------------------------------------
# Switch to non-root user
# ------------------------------------------------------------
USER app

# ------------------------------------------------------------
# HTTPS port
# ------------------------------------------------------------
EXPOSE 8002

# ------------------------------------------------------------
# Run application with HTTPS (TLS always enabled)
# ------------------------------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--ssl-certfile", "/certs/player/player.crt", "--ssl-keyfile", "/certs/player/player.key"]
