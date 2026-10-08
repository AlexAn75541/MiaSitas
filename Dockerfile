# Stage 1: Build
FROM python:3.11-slim-bookworm as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim-bookworm

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Bundle immutable app code into /src (immune to /app or /data host mounts)
WORKDIR /src
COPY . .

# Create fallback mount targets for MCSManager
RUN mkdir -p /data /app

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENV PYTHONUNBUFFERED=1

WORKDIR /src

ENTRYPOINT ["/docker-entrypoint.sh"]
