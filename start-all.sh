#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}Starting BioLink via Docker Compose...${NC}"

cd "$SCRIPT_DIR"
docker compose up -d --build

echo -e "${BLUE}All services started!${NC}"
echo -e "${BLUE}Frontend: http://localhost:3000${NC}"
echo -e "${BLUE}Backend: http://localhost:3001${NC}"
echo -e "${BLUE}Ollama: http://localhost:11434${NC}"
