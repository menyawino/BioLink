#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}Starting BioLink Application...${NC}"

echo -e "${GREEN}Ensuring ports are free...${NC}"
if lsof -nP -iTCP:3001 -sTCP:LISTEN > /dev/null 2>&1; then
    echo -e "${YELLOW}Port 3001 in use; stopping existing process(es)${NC}"
    lsof -t -iTCP:3001 -sTCP:LISTEN | xargs -r kill -TERM 2>/dev/null || true
    sleep 1
fi
if lsof -nP -iTCP:3000 -sTCP:LISTEN > /dev/null 2>&1; then
    echo -e "${YELLOW}Port 3000 in use; stopping existing process(es)${NC}"
    lsof -t -iTCP:3000 -sTCP:LISTEN | xargs -r kill -TERM 2>/dev/null || true
    sleep 1
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n${RED}Shutting down services...${NC}"
    kill 0
    exit
}

trap cleanup SIGINT SIGTERM

echo -e "${GREEN}Checking PostgreSQL connectivity...${NC}"
if ! mamba run -n gcloud pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${YELLOW}PostgreSQL is not accepting connections on localhost:5432${NC}"
    echo -e "${YELLOW}Continuing startup without database. Patient/analytics features will be unavailable.${NC}"
fi

# Start Backend (Python FastAPI)
echo -e "${GREEN}Starting Backend Server (Python FastAPI)...${NC}"
(cd "$SCRIPT_DIR/backend-py" && mamba run -n gcloud bash start.sh) &
BACKEND_PID=$!
sleep 2

# Start Frontend
echo -e "${GREEN}Starting Frontend Server...${NC}"
(cd "$SCRIPT_DIR" && mamba run -n gcloud npm run dev) &
FRONTEND_PID=$!

echo -e "${BLUE}All services started!${NC}"
echo -e "${BLUE}Frontend: http://localhost:3000${NC}"
echo -e "${BLUE}Backend: http://localhost:3001${NC}"
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# Wait for all background processes
wait
