#!/bin/bash

# BioLink Complete Setup and Test Script
# This script sets up the entire BioLink system from scratch

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🚀 BioLink Complete Setup Script${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Docker is running
docker_running() {
    docker info >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}Waiting for $service_name to be ready...${NC}"

    while [ $attempt -le $max_attempts ]; do
        if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $service_name is ready${NC}"
            return 0
        fi
        echo -e "${YELLOW}Attempt $attempt/$max_attempts: $service_name not ready yet...${NC}"
        sleep 10
        ((attempt++))
    done

    echo -e "${RED}✗ $service_name failed to start after $max_attempts attempts${NC}"
    return 1
}

# Step 1: System Requirements Check
echo -e "${BLUE}Step 1: Checking System Requirements${NC}"
echo -e "${BLUE}=========================================${NC}"

# Check OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${GREEN}✓ macOS detected${NC}"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "${GREEN}✓ Linux detected${NC}"
else
    echo -e "${RED}✗ Unsupported OS: $OSTYPE${NC}"
    echo -e "${RED}This script supports macOS and Linux only${NC}"
    exit 1
fi

# Check available memory (rough estimate)
if [[ "$OSTYPE" == "darwin"* ]]; then
    MEM_GB=$(echo "$(sysctl -n hw.memsize) / 1024 / 1024 / 1024" | bc)
else
    MEM_GB=$(free -g | awk 'NR==2{printf "%.0f", $2}')
fi

if [ "$MEM_GB" -lt 8 ]; then
    echo -e "${RED}✗ Insufficient memory: ${MEM_GB}GB detected, minimum 8GB required${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Sufficient memory: ${MEM_GB}GB available${NC}"
fi

# Check available disk space
if [[ "$OSTYPE" == "darwin"* ]]; then
    DISK_GB=$(df -g . | tail -1 | awk '{print $4}')
else
    DISK_GB=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
fi

if [ "$DISK_GB" -lt 10 ]; then
    echo -e "${RED}✗ Insufficient disk space: ${DISK_GB}GB available, minimum 10GB required${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Sufficient disk space: ${DISK_GB}GB available${NC}"
fi

# Check Docker
if ! command_exists docker; then
    echo -e "${RED}✗ Docker not found. Please install Docker Desktop:${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${YELLOW}  brew install --cask docker${NC}"
        echo -e "${YELLOW}  Or download from: https://docs.docker.com/desktop/install/mac-install/${NC}"
    else
        echo -e "${YELLOW}  curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh${NC}"
    fi
    exit 1
else
    echo -e "${GREEN}✓ Docker found${NC}"
fi

# Check Docker Compose
if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo -e "${RED}✗ Docker Compose not found${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Docker Compose found${NC}"
fi

echo ""

# Step 2: Start Docker if not running
echo -e "${BLUE}Step 2: Starting Docker${NC}"
echo -e "${BLUE}=======================${NC}"

if ! docker_running; then
    echo -e "${YELLOW}Docker is not running. Please start Docker Desktop and press Enter to continue...${NC}"
    read -r
    if ! docker_running; then
        echo -e "${RED}✗ Docker is still not running. Please start Docker Desktop manually.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Docker is running${NC}"
fi

echo ""

# Step 3: Setup Environment Files
echo -e "${BLUE}Step 3: Setting up Environment Files${NC}"
echo -e "${BLUE}=====================================${NC}"

# Backend .env
if [ ! -f "backend-py/.env" ]; then
    cp backend-py/.env.example backend-py/.env
    echo -e "${GREEN}✓ Created backend-py/.env${NC}"
else
    echo -e "${GREEN}✓ backend-py/.env already exists${NC}"
fi

# Backend .env.docker
if [ ! -f "backend-py/.env.docker" ]; then
    cp backend-py/.env.example backend-py/.env.docker
    echo -e "${GREEN}✓ Created backend-py/.env.docker${NC}"
else
    echo -e "${GREEN}✓ backend-py/.env.docker already exists${NC}"
fi

# Frontend .env.local
if [ ! -f ".env.local" ]; then
    cp .env .env.local 2>/dev/null || touch .env.local
    echo -e "${GREEN}✓ Created .env.local${NC}"
else
    echo -e "${GREEN}✓ .env.local already exists${NC}"
fi

echo ""

# Step 4: GPU Detection and Configuration
echo -e "${BLUE}Step 4: GPU Detection and Configuration${NC}"
echo -e "${BLUE}=========================================${NC}"

if [[ "$OSTYPE" == "darwin"* ]]; then
    if sysctl -n machdep.cpu.brand_string | grep -q "Apple M"; then
        echo -e "${GREEN}✓ Apple Silicon detected - GPU acceleration will be enabled automatically${NC}"
    else
        echo -e "${YELLOW}Intel Mac detected - GPU acceleration not available${NC}"
    fi
elif command_exists nvidia-smi; then
    echo -e "${GREEN}✓ NVIDIA GPU detected - GPU acceleration available${NC}"
else
    echo -e "${YELLOW}No GPU detected - CPU-only mode${NC}"
fi

echo ""

# Step 5: Build and Start Services
echo -e "${BLUE}Step 5: Building and Starting Services${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "${YELLOW}This may take 10-15 minutes on first run...${NC}"
echo ""

# Stop any existing services
echo -e "${YELLOW}Stopping any existing services...${NC}"
docker compose down --volumes --remove-orphans 2>/dev/null || true

# Start services
echo -e "${YELLOW}Starting all services...${NC}"
docker compose up -d --build

echo ""

# Step 6: Wait for Services to be Ready
echo -e "${BLUE}Step 6: Waiting for Services to be Ready${NC}"
echo -e "${BLUE}==========================================${NC}"

# Wait for Ollama
wait_for_service "http://localhost:11434/api/tags" "Ollama"

# Pull the required model
echo -e "${YELLOW}Pulling Ollama model (llama3.2:3b)...${NC}"
docker exec biolink-ollama ollama pull llama3.2:3b || echo -e "${YELLOW}Model pull may continue in background${NC}"

# Wait for backend
wait_for_service "http://localhost:3001/health" "Backend"

# Wait for frontend
wait_for_service "http://localhost:3000" "Frontend"

echo ""

# Step 7: Database Setup
echo -e "${BLUE}Step 7: Database Setup${NC}"
echo -e "${BLUE}======================${NC}"

echo -e "${YELLOW}Database schema and data will be initialized automatically by the backend...${NC}"

# Wait a bit more for databases to be fully ready
sleep 30

# Check if data was loaded
echo -e "${YELLOW}Checking data status...${NC}"
docker exec biolink-backend python -c "
import sys
sys.path.append('/app')
from sqlalchemy import text, create_engine
from app.config import settings

try:
    engine = create_engine(settings.database_url)
    with engine.begin() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM patients'))
        count = result.fetchone()[0]
        print(f'Data status: {count} records loaded')
except Exception as e:
    print(f'Error checking data: {e}')
" 2>/dev/null || echo -e "${YELLOW}Data check will be performed by backend startup${NC}"

echo ""

# Step 8: Run Tests
echo -e "${BLUE}Step 8: Running Tests${NC}"
echo -e "${BLUE}=====================${NC}"

echo -e "${YELLOW}Running quick test suite...${NC}"
if ./scripts/quick_test.sh; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${YELLOW}⚠ Some tests failed, but services are running${NC}"
fi

echo ""

# Step 9: Final Status and Access URLs
echo -e "${BLUE}Step 9: Setup Complete!${NC}"
echo -e "${BLUE}=========================${NC}"

echo -e "${GREEN}🎉 BioLink is now running!${NC}"
echo ""
echo -e "${GREEN}Access URLs:${NC}"
echo -e "${GREEN}  Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}  Backend API: http://localhost:3001${NC}"
echo -e "${GREEN}  Ollama: http://localhost:11434${NC}"
echo ""
echo -e "${GREEN}To stop services: docker compose down${NC}"
echo -e "${GREEN}To restart: docker compose restart${NC}"
echo -e "${GREEN}To view logs: docker compose logs -f${NC}"
echo ""

# Open browser (macOS)
if [[ "$OSTYPE" == "darwin"* ]] && command_exists open; then
    echo -e "${YELLOW}Opening frontend in browser...${NC}"
    open http://localhost:3000
elif command_exists xdg-open; then
    echo -e "${YELLOW}Opening frontend in browser...${NC}"
    xdg-open http://localhost:3000
else
    echo -e "${YELLOW}Please open http://localhost:3000 in your browser${NC}"
fi

echo ""
echo -e "${GREEN}Setup completed successfully! 🚀${NC}"