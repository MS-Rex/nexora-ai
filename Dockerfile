# Use the latest Python 3.12 slim image with security updates
FROM python:3.12.7-slim-bookworm AS base

# Set environment variables for security and performance
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app \
    # Security: Disable Python's import of user site directory
    PYTHONNOUSERSITE=1

# Install system dependencies with security updates
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Essential build tools
    gcc \
    # Security: Install security updates
    && apt-get upgrade -y \
    # Clean up to reduce image size and attack surface
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Install uv from the latest stable release (pinned for security)
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

# Create non-root user with specific UID/GID for security
RUN groupadd --gid 1001 app \
    && useradd --uid 1001 --gid app --shell /bin/bash --create-home app

# Set work directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml ./
COPY uv.lock ./

# Install Python dependencies in a virtual environment
RUN uv sync --frozen --no-install-project --no-dev

# Copy application code with proper ownership
COPY --chown=app:app . .

# Create necessary directories with proper permissions
RUN mkdir -p logs storage \
    && chown -R app:app /app \
    && chmod -R 755 /app \
    && chmod -R 750 logs storage

# Remove any potential sensitive files
RUN find /app -name "*.pyc" -delete \
    && find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true \
    && rm -rf .git/ .github/ tests/ docs/ scripts/ || true \
    && rm -f .env .env.* docker-compose*.yml Dockerfile .dockerignore || true

# Switch to non-root user
USER app

# Security: Use specific non-privileged port
EXPOSE 8000

# Add .venv/bin to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Improved health check with better error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/v1/health', timeout=5).getcode() == 200 else 1)" \
    || exit 1

# Use exec form for better signal handling and security
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"] 