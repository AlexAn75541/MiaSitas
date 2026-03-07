# Stage 1: Build
FROM python:3.15.0a6-slim-trixie as builder

# Install build dependencies (gcc, Python headers, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy only the requirements file to take advantage of Docker's caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.15.0a6-slim-trixie

# Set the working directory
WORKDIR /app

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.15/site-packages /usr/local/lib/python3.15/site-packages

# Copy the application code
COPY . .

# Create /data directory for MCManager-mounted user data (settings.json, logs, etc.)
RUN mkdir -p /data

# Entrypoint: overlay /data files onto /app before starting
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/docker-entrypoint.sh"]