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

# Function to cleanup on exit
cleanup() {
    echo -e "\n${RED}Shutting down services...${NC}"
    kill 0
    exit
}

trap cleanup SIGINT SIGTERM

# Check if PostgreSQL is already running
if mamba run -n gcloud pg_ctl -D "$SCRIPT_DIR/backend/pgdata" status > /dev/null 2>&1; then
    echo -e "${YELLOW}PostgreSQL is already running${NC}"
else
    # Start PostgreSQL using mamba
    echo -e "${GREEN}Starting PostgreSQL...${NC}"
    mamba run -n gcloud pg_ctl -D "$SCRIPT_DIR/backend/pgdata" -l "$SCRIPT_DIR/backend/pgdata/logfile" start
    sleep 3
fi

# Start Backend (Python FastAPI)
echo -e "${GREEN}Starting Backend Server (Python FastAPI)...${NC}"
(cd "$SCRIPT_DIR/backend-py" && bash start.sh) &
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
