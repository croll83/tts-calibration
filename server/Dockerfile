FROM python:3.12-slim

WORKDIR /app

# Dipendenze sistema per opuslib
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopus0 libopus-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir opuslib

COPY . .

# Crea directory risultati
RUN mkdir -p /data/results

EXPOSE 8200

CMD ["python", "server.py"]
