#!/bin/bash

# BioLink Non-Docker Install Script
# This script sets up BioLink without Docker on macOS and Linux

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
    if [[ "$OSTYPE" != darwin* && "$OSTYPE" != linux* ]]; then
        echo -e "${RED}❌ This script is designed for macOS and Linux only${NC}"
        exit 1
    fi
}

# Function to install Homebrew
install_homebrew() {
    if ! command_exists brew; then
        echo -e "${YELLOW}Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        if [[ "$OSTYPE" == darwin* ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [[ "$OSTYPE" == linux* ]]; then
            echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc
            eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
        fi
    else
        echo -e "${GREEN}✓ Homebrew already installed${NC}"
    fi
}

# Function to install packages
install_packages() {
    echo -e "${YELLOW}Installing required packages...${NC}"

    # Kafka controls:
    # - Set BIOLINK_SKIP_KAFKA=1 to skip Kafka installation (default).
    # - Set BIOLINK_REQUIRE_KAFKA=1 to make Kafka installation mandatory.
    BIOLINK_REQUIRE_KAFKA=${BIOLINK_REQUIRE_KAFKA:-0}
    BIOLINK_SKIP_KAFKA=${BIOLINK_SKIP_KAFKA:-1}
    if [ "$BIOLINK_REQUIRE_KAFKA" -eq 1 ]; then
        BIOLINK_SKIP_KAFKA=0
    fi

    if [[ "$OSTYPE" == darwin* ]]; then
        # macOS with Homebrew
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

    elif [[ "$OSTYPE" == linux* ]]; then
        # Linux (assuming Ubuntu/Debian with apt)
        echo -e "${YELLOW}Updating package lists...${NC}"
        sudo apt update

        # Install PostgreSQL
        if ! command_exists psql; then
            sudo apt install -y postgresql postgresql-contrib
            # Manual start will be done later
        else
            echo -e "${GREEN}✓ PostgreSQL already installed${NC}"
        fi

        # Install Kafka manually (skipped by default)
        if [ "$BIOLINK_SKIP_KAFKA" -eq 1 ]; then
            echo -e "${YELLOW}⏭️  Skipping Kafka installation (BIOLINK_SKIP_KAFKA=1).${NC}"
        elif ! command_exists kafka-server-start; then
            echo -e "${YELLOW}Installing Kafka...${NC}"
            set +e
            KAFKA_OK=1
            sudo apt install -y openjdk-11-jdk wget curl
            
            # Create kafka user and directories
            sudo useradd kafka --shell /bin/bash --home /opt/kafka --create-home 2>/dev/null || true
            sudo mkdir -p /opt/kafka
            sudo chown kafka:kafka /opt/kafka
            
            # Download and extract Kafka as kafka user
            cd /tmp
            KAFKA_VERSION="3.8.0"
            KAFKA_FILE="kafka_2.13-${KAFKA_VERSION}.tgz"
            KAFKA_URL="https://downloads.apache.org/kafka/${KAFKA_VERSION}/${KAFKA_FILE}"
            
            echo -e "${YELLOW}Downloading Kafka from ${KAFKA_URL}...${NC}"
            if ! curl -L -o "${KAFKA_FILE}" "${KAFKA_URL}"; then
                echo -e "${YELLOW}Primary download failed, trying archive.apache.org...${NC}"
                ARCHIVE_URL="https://archive.apache.org/dist/kafka/${KAFKA_VERSION}/${KAFKA_FILE}"
                if ! curl -L -o "${KAFKA_FILE}" "${ARCHIVE_URL}"; then
                    echo -e "${RED}All download attempts failed${NC}"
                    KAFKA_OK=0
                fi
            fi
            
            # Check if download was successful
            if [ "$KAFKA_OK" -eq 1 ]; then
                if [ ! -f "${KAFKA_FILE}" ] || [ ! -s "${KAFKA_FILE}" ]; then
                    echo -e "${RED}Download failed - file not found or empty${NC}"
                    KAFKA_OK=0
                fi
            fi
            
            # Check file size (should be at least 100MB for Kafka)
            if [ "$KAFKA_OK" -eq 1 ]; then
                FILE_SIZE=$(stat -c%s "${KAFKA_FILE}" 2>/dev/null || stat -f%z "${KAFKA_FILE}" 2>/dev/null || echo "0")
                if [ "$FILE_SIZE" -lt 100000000 ]; then
                    echo -e "${RED}Downloaded file is too small (${FILE_SIZE} bytes) - likely not the full Kafka archive${NC}"
                    rm "${KAFKA_FILE}"
                    KAFKA_OK=0
                fi
            fi
            
            # Verify download
            if [ "$KAFKA_OK" -eq 1 ]; then
                echo -e "${YELLOW}Verifying download...${NC}"
                file "${KAFKA_FILE}" | grep -q "gzip compressed data" || {
                    echo -e "${RED}Downloaded file is not a valid gzip archive${NC}"
                    rm "${KAFKA_FILE}"
                    KAFKA_OK=0
                }
            fi

            if [ "$KAFKA_OK" -eq 1 ]; then
                echo -e "${YELLOW}Extracting Kafka...${NC}"
                if sudo tar -xzf "${KAFKA_FILE}" -C /opt/; then
                    # Check what was actually extracted
                    echo -e "${YELLOW}Checking extracted contents...${NC}"
                    ls -la /opt/ | grep kafka || echo "No kafka directories found in /opt/"
                    
                    # Try to find the actual kafka directory (avoid pre-created /opt/kafka)
                    KAFKA_DIR="/opt/kafka_2.13-${KAFKA_VERSION}"
                    if [ ! -d "$KAFKA_DIR" ]; then
                        KAFKA_DIR=$(find /opt -maxdepth 1 -name "kafka_*" -type d | head -1)
                    fi
                    if [ -z "$KAFKA_DIR" ] || [ ! -d "$KAFKA_DIR" ]; then
                        echo -e "${RED}No Kafka directory found in /opt/${NC}"
                        echo -e "${YELLOW}Contents of /opt/:${NC}"
                        ls -la /opt/
                        rm "${KAFKA_FILE}"
                        KAFKA_OK=0
                    else
                        
                        echo -e "${YELLOW}Found Kafka directory: $KAFKA_DIR${NC}"
                        sudo ln -sfn "$KAFKA_DIR" /opt/kafka
                        sudo chown -R kafka:kafka "$KAFKA_DIR"
                        sudo chown -R kafka:kafka /opt/kafka
                        sudo mkdir -p /opt/kafka/logs
                        sudo chown kafka:kafka /opt/kafka/logs
                        
                        # Configure Kafka for single-node setup
                        if [ -f "/opt/kafka/config/server.properties" ]; then
                            sudo sed -i 's/broker.id=0/broker.id=0/' /opt/kafka/config/server.properties
                            sudo sed -i 's/#listeners=PLAINTEXT:\/\/:9092/listeners=PLAINTEXT:\/\/localhost:9092/' /opt/kafka/config/server.properties
                            sudo sed -i 's/#advertised.listeners=PLAINTEXT:\/\/your.host.name:9092/advertised.listeners=PLAINTEXT:\/\/localhost:9092/' /opt/kafka/config/server.properties
                            
                            echo -e "${GREEN}✓ Kafka installed and configured successfully${NC}"
                        else
                            echo -e "${RED}Kafka config file not found at /opt/kafka/config/server.properties${NC}"
                            echo -e "${YELLOW}Checking Kafka directory structure...${NC}"
                            find /opt/kafka -name "server.properties" 2>/dev/null || echo "server.properties not found"
                            KAFKA_OK=0
                        fi
                    fi
                else
                    echo -e "${RED}Failed to extract Kafka archive${NC}"
                    rm "${KAFKA_FILE}"
                    KAFKA_OK=0
                fi
            else
                echo -e "${RED}Downloaded file is empty or missing${NC}"
                rm -f "${KAFKA_FILE}"
                KAFKA_OK=0
            fi

            set -e
            if [ "$KAFKA_OK" -ne 1 ]; then
                if [ "$BIOLINK_REQUIRE_KAFKA" -eq 1 ]; then
                    echo -e "${RED}Kafka installation failed and BIOLINK_REQUIRE_KAFKA=1 is set${NC}"
                    exit 1
                fi
                echo -e "${YELLOW}⚠️  Kafka installation failed. Continuing without Kafka.${NC}"
            fi
        else
            echo -e "${GREEN}✓ Kafka already installed${NC}"
        fi

        # Install Ollama
        if ! command_exists ollama; then
            echo -e "${YELLOW}Installing Ollama...${NC}"
            sudo apt install -y zstd
            curl -fsSL https://ollama.ai/install.sh | sh
        else
            echo -e "${GREEN}✓ Ollama already installed${NC}"
        fi

        # Install Python 3.11+
        if ! command_exists python3.11; then
            sudo apt install -y python3.11 python3.11-venv
        else
            echo -e "${GREEN}✓ Python 3.11 already installed${NC}"
        fi

        # Ensure pip is available for Python 3.11
        if ! command_exists pip3.11; then
            echo -e "${YELLOW}Installing pip for Python 3.11...${NC}"
            if ! python3.11 -m ensurepip --upgrade >/dev/null 2>&1; then
                sudo apt install -y python3-pip
            fi
        fi

        # Install Node.js
        if ! command_exists node; then
            curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
            sudo apt install -y nodejs
        else
            echo -e "${GREEN}✓ Node.js already installed${NC}"
        fi
    fi

    echo -e "${GREEN}✓ All packages installed${NC}"
}

# Function to setup databases
setup_databases() {
    echo -e "${YELLOW}Setting up databases...${NC}"

    if [[ "$OSTYPE" == darwin* ]]; then
        # macOS
        brew services start postgresql@16
        sleep 5

        # Create databases as current user
        psql -h localhost -c "CREATE DATABASE biolink;" 2>/dev/null || echo "Database biolink already exists"
        psql -h localhost -c "CREATE DATABASE biolink_vector;" 2>/dev/null || echo "Database biolink_vector already exists"

        # Install pgvector extension
        psql -h localhost -d biolink_vector -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || echo "pgvector extension already installed"

    elif [[ "$OSTYPE" == linux* ]]; then
        # Linux - manual PostgreSQL start
        if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
            echo -e "${YELLOW}Starting PostgreSQL manually...${NC}"
            sudo touch /tmp/postgres.log
            sudo chown postgres:postgres /tmp/postgres.log
            PG_CONFIG_FILE="/etc/postgresql/14/main/postgresql.conf"
            PG_HBA_FILE="/etc/postgresql/14/main/pg_hba.conf"
            PG_IDENT_FILE="/etc/postgresql/14/main/pg_ident.conf"
            PG_OPTS=""
            if [ -f "$PG_CONFIG_FILE" ]; then
                PG_OPTS="-o -c config_file=$PG_CONFIG_FILE -c hba_file=$PG_HBA_FILE -c ident_file=$PG_IDENT_FILE"
            fi
            (cd /tmp && sudo -u postgres /usr/lib/postgresql/14/bin/pg_ctl -w -D /var/lib/postgresql/14/main -l /tmp/postgres.log $PG_OPTS start)
            sleep 5
        fi

        if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
            echo -e "${RED}PostgreSQL failed to start. See /tmp/postgres.log${NC}"
            if [ -f /tmp/postgres.log ]; then
                echo -e "${YELLOW}Last 50 lines of /tmp/postgres.log:${NC}"
                tail -n 50 /tmp/postgres.log || true
            fi
        fi

        # Create databases as postgres user
        (cd /tmp && sudo -u postgres psql -c "CREATE DATABASE biolink;" 2>/dev/null || echo "Database biolink already exists")
        (cd /tmp && sudo -u postgres psql -c "CREATE DATABASE biolink_vector;" 2>/dev/null || echo "Database biolink_vector already exists")

        # Install pgvector extension (if available)
        (cd /tmp && sudo -u postgres psql -d biolink_vector -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || echo "pgvector extension not available or already installed")
    fi

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

    if [[ "$OSTYPE" == darwin* ]]; then
        # macOS using brew services
        brew services start postgresql@16
        brew services start zookeeper
        brew services start kafka
        brew services start ollama
    elif [[ "$OSTYPE" == linux* ]]; then
        # Linux using manual service management (works in all environments)
        # Start PostgreSQL manually if not running
        if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
            sudo -u postgres /usr/lib/postgresql/14/bin/pg_ctl -D /var/lib/postgresql/14/main -l /tmp/postgres.log start &
            POSTGRES_PID=$!
            echo $POSTGRES_PID > /tmp/postgres.pid
            sleep 5
        fi

        # Start Kafka services manually (works in containers/VMs without systemd)
        if command -v kafka-server-start >/dev/null 2>&1 && [ -d "/opt/kafka" ]; then
            echo -e "${YELLOW}Starting Kafka manually...${NC}"
            # Start Zookeeper
            sudo -u kafka /opt/kafka/bin/zookeeper-server-start.sh /opt/kafka/config/zookeeper.properties > /tmp/zookeeper.log 2>&1 &
            ZOOKEEPER_PID=$!
            echo $ZOOKEEPER_PID > /tmp/zookeeper.pid
            sleep 5
            
            # Start Kafka
            sudo -u kafka /opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server.properties > /tmp/kafka.log 2>&1 &
            KAFKA_PID=$!
            echo $KAFKA_PID > /tmp/kafka.pid
            sleep 5
            
            echo -e "${GREEN}✓ Kafka services started (PIDs: Zookeeper=$ZOOKEEPER_PID, Kafka=$KAFKA_PID)${NC}"
        fi

        # Start Ollama manually
        if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            ollama serve > /tmp/ollama.log 2>&1 &
            OLLAMA_PID=$!
            echo $OLLAMA_PID > /tmp/ollama.pid
            sleep 5
        fi
    fi

    echo -e "${GREEN}✓ Services started${NC}"
}

# Function to load data
load_data() {
    echo -e "${YELLOW}Loading initial data...${NC}"

    if [[ "$OSTYPE" == linux* ]]; then
        if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
            echo -e "${YELLOW}Starting PostgreSQL for data load...${NC}"
            sudo touch /tmp/postgres.log
            sudo chown postgres:postgres /tmp/postgres.log
            PG_CONFIG_FILE="/etc/postgresql/14/main/postgresql.conf"
            PG_HBA_FILE="/etc/postgresql/14/main/pg_hba.conf"
            PG_IDENT_FILE="/etc/postgresql/14/main/pg_ident.conf"
            PG_OPTS=""
            if [ -f "$PG_CONFIG_FILE" ]; then
                PG_OPTS="-o -c config_file=$PG_CONFIG_FILE -c hba_file=$PG_HBA_FILE -c ident_file=$PG_IDENT_FILE"
            fi
            (cd /tmp && sudo -u postgres /usr/lib/postgresql/14/bin/pg_ctl -w -D /var/lib/postgresql/14/main -l /tmp/postgres.log $PG_OPTS start)
            sleep 5
        fi
    fi

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
    echo -e "${YELLOW}Stopping application and services...${NC}"

    # Stop BioLink application processes
    if [ -f "backend.pid" ]; then
        kill $(cat backend.pid) 2>/dev/null || true
        rm backend.pid
    fi

    if [ -f "frontend.pid" ]; then
        kill $(cat frontend.pid) 2>/dev/null || true
        rm frontend.pid
    fi

    # Stop services on Linux
    if [[ "$OSTYPE" == linux* ]]; then
        # Stop PostgreSQL
        if [ -f "/tmp/postgres.pid" ]; then
            sudo -u postgres /usr/lib/postgresql/14/bin/pg_ctl -D /var/lib/postgresql/14/main stop &
            rm /tmp/postgres.pid
        fi

        # Stop Kafka services manually
        if [ -f "/tmp/kafka.pid" ]; then
            kill $(cat /tmp/kafka.pid) 2>/dev/null || true
            rm /tmp/kafka.pid
        fi
        if [ -f "/tmp/zookeeper.pid" ]; then
            kill $(cat /tmp/zookeeper.pid) 2>/dev/null || true
            rm /tmp/zookeeper.pid
        fi

        # Stop Ollama
        if [ -f "/tmp/ollama.pid" ]; then
            kill $(cat /tmp/ollama.pid) 2>/dev/null || true
            rm /tmp/ollama.pid
        fi
    fi

    echo -e "${GREEN}✓ Application and services stopped${NC}"
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
        if [[ "$OSTYPE" == darwin* ]]; then
            install_homebrew
        fi
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
esac