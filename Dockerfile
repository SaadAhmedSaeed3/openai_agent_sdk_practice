# syntax=docker/dockerfile:1
FROM python:3.13-slim

# System dependencies: ffmpeg (video encoding) + Playwright Chromium deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    # Chromium runtime dependencies
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpangocairo-1.0-0 libpango-1.0-0 \
    libcairo2 libatspi2.0-0 libgtk-3-0 libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python dependencies via uv (uses lockfile for reproducibility)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Install Playwright Chromium browser
RUN uv run playwright install chromium

# Copy project source
COPY . .

# Ensure output directories exist
RUN mkdir -p output/frames presentation_creator/refrence_txt

ENTRYPOINT ["uv", "run", "python", "main.py"]
