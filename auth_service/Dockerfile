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
# TLS directories (certs are bind-mounted by docker-compose)
# ------------------------------------------------------------
RUN mkdir -p /certs/ca /certs/auth

# ------------------------------------------------------------
# Application code
# (will be overridden by volume mount in docker-compose)
# ------------------------------------------------------------
COPY . .

# ------------------------------------------------------------
# Networking
# ------------------------------------------------------------
EXPOSE 8001

# ------------------------------------------------------------
# Run with TLS
# ------------------------------------------------------------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--ssl-certfile", "/certs/auth/auth.crt", "--ssl-keyfile", "/certs/auth/auth.key"]
