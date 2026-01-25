# Docker Directory

This directory contains Docker-related configuration files.

## Files

- `Dockerfile.frontend` - Dockerfile for building the frontend container

## Related Files

Docker Compose files are located in the project root:
- `docker-compose.yml` - Main docker compose configuration
- `docker-compose.rag.yml` - RAG-specific services

## Usage

The frontend Dockerfile is used by the main docker-compose.yml file. To build manually:

```bash
docker build -f docker/Dockerfile.frontend -t biolink-frontend .
```