#!/bin/bash

# Start all BioLink services (wrapper)
set -e

echo "Starting all services (via docker compose)..."
docker compose up -d --build

echo "All services started"