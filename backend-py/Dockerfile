FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.docker.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.docker.txt

# Copy application code
COPY app ./app
COPY tests ./tests
COPY start.sh ./

# Create non-root user for security
RUN useradd -m -u 1000 biolink && chown -R biolink:biolink /app
USER biolink

EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys, urllib.request; urllib.request.urlopen('http://localhost:3001/health', timeout=5); sys.exit(0)" || exit 1

# Production: no --reload.  For dev, docker-compose bind-mounts app/ and
# overrides CMD to add --reload.
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3001"]
