FROM python:3.11-slim

WORKDIR /app

# ------------------------------------------------------------
# System dependencies
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
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
# TLS directories (certs are bind-mounted by docker-compose)
# ------------------------------------------------------------
RUN mkdir -p /certs/ca /certs/auth

# ------------------------------------------------------------
# Application code
# (will be overridden by volume mount in docker-compose)
# ------------------------------------------------------------
COPY --chown=app:app . .

# ------------------------------------------------------------
# Switch to non-root user
# ------------------------------------------------------------
USER app

# ------------------------------------------------------------
# Networking
# ------------------------------------------------------------
EXPOSE 8001

# ------------------------------------------------------------
# Run with TLS
# ------------------------------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--ssl-certfile", "/certs/auth_service/auth_service.crt", "--ssl-keyfile", "/certs/auth_service/auth_service.key"]
