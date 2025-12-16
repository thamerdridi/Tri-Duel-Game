FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn httpx

COPY app /app

EXPOSE 8443

CMD ["uvicorn", "main:app",  "--host", "0.0.0.0", "--port", "8443", "--ssl-certfile", "/certs/gateway/gateway.crt", "--ssl-keyfile", "/certs/gateway/gateway.key"]
