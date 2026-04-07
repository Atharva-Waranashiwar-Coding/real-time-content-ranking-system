#!/usr/bin/env python3
"""Generate requirements.txt and Dockerfile for each service."""

from pathlib import Path

services = [
    "api-gateway",
    "user-service",
    "content-service",
    "interaction-service",
    "feed-service",
    "ranking-service",
    "experimentation-service",
    "analytics-service",
    "feature-processor",
]

base_path = Path("/Users/atharvawaranashiwar/Documents/Projects/content_ranking_system/services")

# Common requirements
requirements_content = """fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
sqlalchemy==2.0.23
asyncpg==0.29.0
psycopg2-binary==2.9.9
redis==5.0.1
httpx==0.25.2
confluent-kafka==2.3.0
pythonjsonlogger==2.0.7
python-dotenv==1.0.0
prometheus-client==0.19.0
aioredis==2.0.1
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.12.0
ruff==0.1.8
"""

dockerfile_template = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variable
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \\
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

for service in services:
    service_path = base_path / service
    
    # Create requirements.txt
    req_file = service_path / "requirements.txt"
    req_file.write_text(requirements_content)
    
    # Create Dockerfile
    docker_file = service_path / "Dockerfile"
    docker_file.write_text(dockerfile_template)
    
    print(f"✓ Created requirements.txt and Dockerfile for {service}")

print("\n✓ All Dockerfiles and requirements.txt created")
