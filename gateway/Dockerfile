FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn httpx

# ------------------------------------------------------------
# Create non-root user
# ------------------------------------------------------------
RUN addgroup --system app && adduser --system --ingroup app app

# ------------------------------------------------------------
# Prepare directories for TLS cert bind mounts
# ------------------------------------------------------------
RUN mkdir -p /certs/ca /certs/gateway

# ------------------------------------------------------------
# Application code
# ------------------------------------------------------------
COPY --chown=app:app app /app

# ------------------------------------------------------------
# Switch to non-root user
# ------------------------------------------------------------
USER app

EXPOSE 8443

CMD ["uvicorn", "main:app",  "--host", "0.0.0.0", "--port", "8443", "--ssl-certfile", "/certs/gateway/gateway.crt", "--ssl-keyfile", "/certs/gateway/gateway.key"]
