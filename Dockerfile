# --- Stage 1: Build Frontend ---
FROM node:20-slim AS frontend-builder
WORKDIR /web
COPY web/package*.json ./
# Use NPM Mirror
RUN npm config set registry https://registry.npmmirror.com
RUN npm install
COPY web/ ./
RUN npm run build

# --- Stage 2: Build Python Dependencies ---
FROM python:3.10-slim AS python-builder
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Change APT source to Tsinghua Mirror
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
# Use PyPI Mirror
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt

# --- Stage 3: Final Runtime Image ---
FROM python:3.10-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Change APT source to Tsinghua Mirror
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# Install runtime dependencies ONLY (ffmpeg, curl for healthcheck)
# No gcc or build tools needed here
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=python-builder /opt/venv /opt/venv

# Copy frontend artifacts
COPY --from=frontend-builder /web/dist ./web/dist

# Copy application code
COPY app ./app
COPY init_db.py .
COPY run_worker.py .

# Create data directory
RUN mkdir -p /app/data

# Expose API port
EXPOSE 8712

# Setup entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
