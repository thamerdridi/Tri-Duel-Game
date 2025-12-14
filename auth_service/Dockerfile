FROM python:3.11-slim

# ==========================
# SECURITY: NON-ROOT USER
# ==========================
RUN useradd -m authuser

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ownership
RUN chown -R authuser:authuser /app

USER authuser

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
