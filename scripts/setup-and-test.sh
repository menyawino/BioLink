#!/bin/bash

# Lightweight setup-and-test wrapper (docker-first)
set -e

echo "Building and starting services (docker compose)..."
docker compose up -d --build

# Wait for services
wait_for() {
  url=$1; name=$2; max=30; i=0
  until curl -sSf "$url" >/dev/null 2>&1 || [ $i -ge $max ]; do
    printf "."; sleep 2; i=$((i+1));
  done
  if [ $i -ge $max ]; then
    echo "\n$name failed to respond in time"
    return 1
  fi
  echo "\n$name ready"
}

echo "Waiting for backend..."
wait_for http://localhost:3001/health Backend

echo "Waiting for frontend..."
wait_for http://localhost:3000 Frontend

# Run quick tests if available
if [ -f "./scripts/quick_test.sh" ]; then
  echo "Running quick tests..."
  bash ./scripts/quick_test.sh || echo "Quick tests had failures"
else
  echo "No quick_test.sh found"
fi

echo "Setup + tests complete"