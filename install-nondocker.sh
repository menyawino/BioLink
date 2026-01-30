#!/bin/bash

# BioLink Non-Docker Install Script
# This script sets up BioLink without Docker on macOS

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

echo -e "${BLUE}🚀 BioLink Non-Docker Setup Script${NC}"
echo -e "${BLUE}===================================${NC}"
echo ""

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check OS
check_os() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo -e "${RED}❌ This script is designed for macOS only${NC}"
        exit 1
    fi
}

# Function to install Homebrew
install_homebrew() {
    if ! command_exists brew; then
        echo -e "${YELLOW}Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        echo -e "${GREEN}✓ Homebrew already installed${NC}"
    fi
}

# Function to install packages
install_packages() {
    echo -e "${YELLOW}Installing required packages...${NC}"

    # Update Homebrew
    brew update

    # Install PostgreSQL
    if ! command_exists psql; then
        brew install postgresql@16
        brew services start postgresql@16
        sleep 2
        /opt/homebrew/opt/postgresql@16/bin/createuser -s postgres 2>/dev/null || true
    else
        echo -e "${GREEN}✓ PostgreSQL already installed${NC}"
    fi

    # Install Kafka
    if ! command_exists kafka-server-start; then
        brew install kafka
    else
        echo -e "${GREEN}✓ Kafka already installed${NC}"
    fi

    # Install Ollama
    if ! command_exists ollama; then
        brew install ollama
        brew services start ollama
    else
        echo -e "${GREEN}✓ Ollama already installed${NC}"
    fi

    # Install Python 3.11+
    if ! command_exists python3.11; then
        brew install python@3.11
    else
        echo -e "${GREEN}✓ Python 3.11 already installed${NC}"
    fi

    # Install Node.js
    if ! command_exists node; then
        brew install node
    else
        echo -e "${GREEN}✓ Node.js already installed${NC}"
    fi

    # Install pgvector extension dependencies
    brew install postgresql@16  # Ensure we have the right version

    echo -e "${GREEN}✓ All packages installed${NC}"
}

# Function to setup databases
setup_databases() {
    echo -e "${YELLOW}Setting up databases...${NC}"

    # Start PostgreSQL if not running
    brew services start postgresql@16

    # Wait for PostgreSQL to start
    sleep 5

    # Create databases
    psql -h localhost -U postgres -c "CREATE DATABASE biolink;" 2>/dev/null || echo "Database biolink already exists"
    psql -h localhost -U postgres -c "CREATE DATABASE biolink_vector;" 2>/dev/null || echo "Database biolink_vector already exists"

    # Install pgvector extension
    psql -h localhost -U postgres -d biolink_vector -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || echo "pgvector extension already installed"

    echo -e "${GREEN}✓ Databases setup complete${NC}"
}

# Function to setup Python environment
setup_python() {
    echo -e "${YELLOW}Setting up Python environment...${NC}"

    cd backend-py

    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3.11 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Install requirements
    pip install -r requirements.txt

    # Copy environment file
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit backend-py/.env with your database credentials${NC}"
    fi

    cd ..
    echo -e "${GREEN}✓ Python environment setup complete${NC}"
}

# Function to setup Node.js environment
setup_nodejs() {
    echo -e "${YELLOW}Setting up Node.js environment...${NC}"

    # Install dependencies
    npm install

    echo -e "${GREEN}✓ Node.js environment setup complete${NC}"
}

# Function to setup Ollama models
setup_ollama() {
    echo -e "${YELLOW}Setting up Ollama models...${NC}"

    # Pull required models
    ollama pull llama3.2:3b || echo "Model llama3.2:3b already available"

    echo -e "${GREEN}✓ Ollama models setup complete${NC}"
}

# Function to start services
start_services() {
    echo -e "${YELLOW}Starting services...${NC}"

    # Start PostgreSQL
    brew services start postgresql@16

    # Start Kafka (Zookeeper + Kafka)
    brew services start zookeeper
    brew services start kafka

    # Start Ollama
    brew services start ollama

    echo -e "${GREEN}✓ Services started${NC}"
}

# Function to load data
load_data() {
    echo -e "${YELLOW}Loading initial data...${NC}"

    cd backend-py
    source venv/bin/activate

    # Run data loading script
    python -c "
from sqlalchemy import text, create_engine
from app.config import settings
from pathlib import Path
engine = create_engine(settings.database_url.replace('localhost', '127.0.0.1'))
with engine.begin() as conn:
    try:
        result = conn.execute(text('SELECT COUNT(*) FROM patients'))
        count = result.fetchone()[0]
        if count == 0:
            print('Loading reduced dataset...')
            from app.load_reduced_data import load_reduced_data
            load_reduced_data()
        else:
            print(f'Data already loaded: {count} records')
    except:
        print('Loading reduced dataset...')
        from app.load_reduced_data import load_reduced_data
        load_reduced_data()
"

    cd ..
    echo -e "${GREEN}✓ Data loading complete${NC}"
}

# Function to start application
start_application() {
    echo -e "${YELLOW}Starting BioLink application...${NC}"

    # Start backend in background
    cd backend-py
    source venv/bin/activate
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload > backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > backend.pid
    cd ..

    # Start frontend in background
    nohup npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > frontend.pid

    echo -e "${GREEN}✓ Application started${NC}"
    echo -e "${GREEN}📱 Frontend: http://localhost:5173${NC}"
    echo -e "${GREEN}🔧 Backend API: http://localhost:3001${NC}"
    echo -e "${GREEN}📚 API Docs: http://localhost:3001/docs${NC}"
}

# Function to stop application
stop_application() {
    echo -e "${YELLOW}Stopping application...${NC}"

    if [ -f "backend.pid" ]; then
        kill $(cat backend.pid) 2>/dev/null || true
        rm backend.pid
    fi

    if [ -f "frontend.pid" ]; then
        kill $(cat frontend.pid) 2>/dev/null || true
        rm frontend.pid
    fi

    echo -e "${GREEN}✓ Application stopped${NC}"
}

# Function to show status
show_status() {
    echo -e "${BLUE}BioLink Status${NC}"
    echo -e "${BLUE}==============${NC}"

    # Check services
    if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL running${NC}"
    else
        echo -e "${RED}✗ PostgreSQL not running${NC}"
    fi

    if nc -z localhost 9092 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Kafka running${NC}"
    else
        echo -e "${RED}✗ Kafka not running${NC}"
    fi

    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama running${NC}"
    else
        echo -e "${RED}✗ Ollama not running${NC}"
    fi

    if curl -s http://localhost:3001/docs >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend running${NC}"
    else
        echo -e "${RED}✗ Backend not running${NC}"
    fi

    if nc -z localhost 5173 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend running${NC}"
    else
        echo -e "${RED}✗ Frontend not running${NC}"
    fi
}

# Main script logic
case "${1:-install}" in
    "install")
        check_os
        install_homebrew
        install_packages
        setup_databases
        setup_python
        setup_nodejs
        setup_ollama
        load_data
        echo -e "${GREEN}🎉 Installation complete! Run '$0 start' to start the application${NC}"
        ;;
    "start")
        start_services
        start_application
        echo -e "${GREEN}🚀 BioLink is running!${NC}"
        echo -e "${GREEN}📱 Open http://localhost:5173 in your browser${NC}"
        ;;
    "stop")
        stop_application
        ;;
    "status")
        show_status
        ;;
    "restart")
        stop_application
        start_services
        start_application
        ;;
    *)
        echo "Usage: $0 [install|start|stop|status|restart]"
        echo ""
        echo "Commands:"
        echo "  install  - Install all dependencies and setup databases"
        echo "  start    - Start all services and the application"
        echo "  stop     - Stop the application"
        echo "  status   - Show status of all services"
        echo "  restart  - Restart all services and application"
        exit 1
        ;;
esac</content>
<parameter name="filePath">/Users/menyawino/Playground/BioLink/Code/install-nondocker.sh