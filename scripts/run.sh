#!/bin/bash

# BioLink Quick Start Script (moved to scripts/)
# Starts all services assuming setup is already complete

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting BioLink Services${NC}"
echo -e "${BLUE}===========================${NC}"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${YELLOW}Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

# Start services
echo -e "${YELLOW}Starting all services...${NC}"
docker compose up -d --pull never

echo -e "${GREEN}✓ Services started!${NC}"
echo ""
echo -e "${GREEN}Access URLs:${NC}"
echo -e "${GREEN}  Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}  Backend: http://localhost:3001${NC}"
echo -e "${GREEN}  Ollama: http://localhost:11434${NC}"
echo ""
echo -e "${GREEN}To view logs: docker compose logs -f${NC}"
echo -e "${GREEN}To stop: docker compose down${NC}"

# Open browser on macOS
if [[ "$OSTYPE" == "darwin"* ]] && command -v open >/dev/null 2>&1; then
    echo -e "${YELLOW}Opening frontend in browser...${NC}"
    open http://localhost:3000
fi