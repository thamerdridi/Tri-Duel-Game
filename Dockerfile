# Base image: lightweight Python
FROM python:3.11-slim

WORKDIR /app

# Install C dependencies for some libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY game_app/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./game_app /app/game_app

EXPOSE 8000

CMD ["uvicorn", "game_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
