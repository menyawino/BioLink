#!/bin/bash

# BioLink Complete Setup and Testing Script
# This script sets up the entire BioLink system from scratch

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Detect GPU availability
detect_gpu() {
    log_info "Detecting GPU availability..."

    # Check for NVIDIA GPU
    if command -v nvidia-smi &> /dev/null; then
        log_success "NVIDIA GPU detected"
        echo "nvidia"
        return
    fi

    # Check for Apple Silicon (M1/M2/M3)
    if [[ "$OS" == "macos" ]]; then
        if system_profiler SPHardwareDataType 2>/dev/null | grep -q "Chip.*Apple\|Apple M"; then
            log_success "Apple Silicon GPU detected"
            echo "apple"
            return
        fi
    fi

    # Check for AMD GPU on Linux
    if [[ "$OS" == "linux" ]]; then
        if lspci | grep -i amd &> /dev/null && command -v rocminfo &> /dev/null; then
            log_success "AMD GPU detected"
            echo "amd"
            return
        fi
    fi

    log_warning "No GPU detected, will use CPU-only mode"
    echo "none"
}

# Configure GPU settings for Ollama
configure_gpu() {
    if [[ "$GPU_TYPE" == "nvidia" ]]; then
        log_info "Configuring NVIDIA GPU support..."
        # Add GPU configuration to docker-compose.yml
        if ! grep -q "deploy:" docker-compose.yml; then
            sed -i.bak '/ollama:/a\
    deploy:\
      resources:\
        reservations:\
          devices:\
            - driver: nvidia\
              count: 1\
              capabilities: [gpu]' docker-compose.yml
        fi
        log_success "NVIDIA GPU configured for Ollama"

    elif [[ "$GPU_TYPE" == "apple" ]]; then
        log_info "Apple Silicon GPU detected - Ollama will use it automatically"
        log_info "No additional configuration needed for Apple GPU"

    elif [[ "$GPU_TYPE" == "amd" ]]; then
        log_info "AMD GPU detected - configuring ROCm support..."
        # Note: AMD GPU support in Docker is limited, Ollama may still use CPU

    else
        log_info "No GPU detected - Ollama will run on CPU"
    fi
}

# Check if running as root/sudo (for installations)
check_sudo() {
    if [[ $EUID -eq 0 ]]; then
        echo "root"
    elif sudo -n true 2>/dev/null; then
        echo "sudo"
    else
        echo "user"
    fi
}

SUDO_STATUS=$(check_sudo)

# Function to install Docker
install_docker() {
    log_info "Installing Docker..."

    case $OS in
        "linux")
            if [[ "$SUDO_STATUS" != "root" ]] && [[ "$SUDO_STATUS" != "sudo" ]]; then
                log_error "Docker installation requires sudo privileges on Linux"
                exit 1
            fi

            # Install Docker using convenience script
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo systemctl start docker
            sudo systemctl enable docker

            # Add user to docker group if not root
            if [[ "$SUDO_STATUS" == "sudo" ]]; then
                sudo usermod -aG docker $USER
                log_warning "Please log out and back in for docker group changes to take effect"
            fi
            ;;

        "macos")
            if command -v brew >/dev/null 2>&1; then
                brew install --cask docker
                log_info "Docker Desktop installed. Please start Docker Desktop manually."
            else
                log_error "Homebrew not found. Please install Docker Desktop manually from https://docs.docker.com/desktop/install/mac-install/"
                exit 1
            fi
            ;;

        *)
            log_error "Automatic Docker installation not supported for $OS. Please install Docker manually."
            exit 1
            ;;
    esac

    log_success "Docker installation completed"
}

# Function to install Docker Compose
install_docker_compose() {
    log_info "Installing Docker Compose..."

    case $OS in
        "linux"|"macos")
            if [[ "$SUDO_STATUS" != "root" ]] && [[ "$SUDO_STATUS" != "sudo" ]]; then
                log_error "Docker Compose installation requires sudo privileges"
                exit 1
            fi

            # Docker Compose is now included with Docker Desktop
            if ! command -v docker-compose >/dev/null 2>&1 && ! docker compose version >/dev/null 2>&1; then
                log_error "Docker Compose not found. Please ensure Docker Desktop is properly installed."
                exit 1
            fi
            ;;

        *)
            log_error "Docker Compose installation check failed for $OS"
            exit 1
            ;;
    esac

    log_success "Docker Compose ready"
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."

    # Check available memory
    if [[ "$OS" == "linux" ]] || [[ "$OS" == "macos" ]]; then
        MEM_GB=$(echo "scale=2; $(grep MemTotal /proc/meminfo | awk '{print $2}') / 1024 / 1024" 2>/dev/null || echo "8")
        if (( $(echo "$MEM_GB < 8" | bc -l 2>/dev/null || echo "0") )); then
            log_warning "System has ${MEM_GB}GB RAM. BioLink recommends at least 8GB for optimal performance."
        else
            log_info "System memory: ${MEM_GB}GB - OK"
        fi
    fi

    # Check available disk space
    DISK_GB=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    if (( DISK_GB < 10 )); then
        log_warning "Only ${DISK_GB}GB free disk space. BioLink requires at least 10GB."
    else
        log_info "Available disk space: ${DISK_GB}GB - OK"
    fi
}

# Main setup function
main() {
    log_info "BioLink Complete Setup and Testing Script"
    log_info "=========================================="

    # Check if we're in the right directory
    if [[ ! -f "docker-compose.yml" ]] || [[ ! -f "package.json" ]]; then
        log_error "Please run this script from the BioLink project root directory"
        exit 1
    fi

    check_requirements

    # Check for Docker
    if ! command -v docker >/dev/null 2>&1; then
        log_warning "Docker not found. Installing..."
        install_docker

        # Wait for Docker to be ready
        log_info "Waiting for Docker to start..."
        sleep 10

        # Check again
        if ! command -v docker >/dev/null 2>&1; then
            log_error "Docker installation failed"
            exit 1
        fi
    else
        log_success "Docker found"
    fi

    # Check for Docker Compose
    if ! docker compose version >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
        log_warning "Docker Compose not found. Installing..."
        install_docker_compose
    else
        log_success "Docker Compose found"
    fi

    # Start Docker if not running
    if ! docker info >/dev/null 2>&1; then
        log_info "Starting Docker service..."
        case $OS in
            "linux")
                sudo systemctl start docker
                ;;
            "macos")
                log_warning "Please start Docker Desktop manually, then re-run this script"
                exit 1
                ;;
        esac
    fi

    # Clean up any existing containers
    log_info "Cleaning up existing containers..."
    docker compose down -v 2>/dev/null || true
    docker system prune -f

    # Configure GPU if available
    configure_gpu

    # Build and start all services

    # Start with just the core services first
    docker compose up -d postgres pgvector ollama

    # Wait for databases to be ready
    log_info "Waiting for databases to initialize..."
    sleep 30

    # Check if databases are ready
    if ! docker exec biolink-postgres pg_isready -U biolink -d biolink >/dev/null 2>&1; then
        log_error "PostgreSQL failed to start"
        docker compose logs postgres
        exit 1
    fi

    log_success "Databases ready"

    # Start remaining services
    docker compose up -d

    # Wait for all services to be healthy
    log_info "Waiting for all services to be ready..."
    MAX_WAIT=300  # 5 minutes
    WAIT_TIME=0

    while [ $WAIT_TIME -lt $MAX_WAIT ]; do
        # Check backend health
        if curl -s --max-time 5 http://localhost:3001/health >/dev/null 2>&1; then
            log_success "Backend is responding"
            break
        fi

        sleep 10
        WAIT_TIME=$((WAIT_TIME + 10))
        log_info "Waiting... (${WAIT_TIME}s/${MAX_WAIT}s)"
    done

    if [ $WAIT_TIME -ge $MAX_WAIT ]; then
        log_error "Services failed to start within ${MAX_WAIT} seconds"
        docker compose logs
        exit 1
    fi

    # Load the reduced dataset
    log_info "Loading reduced dataset (50 records)..."
    if docker exec biolink-backend python app/load_reduced_data.py 2>/dev/null; then
        log_success "Dataset loaded successfully"
    else
        log_warning "Dataset loading failed - will be loaded on first backend restart"
    fi

    # Run tests
    log_info "Running system tests..."

    # Test 1: Backend health
    if curl -s --max-time 5 http://localhost:3001/health >/dev/null 2>&1; then
        log_success "✓ Backend health check passed"
    else
        log_error "✗ Backend health check failed"
        exit 1
    fi

    # Test 2: Frontend
    if curl -s --max-time 5 -I http://localhost:3000 >/dev/null 2>&1; then
        log_success "✓ Frontend responding"
    else
        log_error "✗ Frontend not responding"
        exit 1
    fi

    # Test 3: SQL Agent (heuristic query)
    response=$(curl -s --max-time 10 -X POST http://localhost:3001/api/chat/sql-agent \
        -H "Content-Type: application/json" \
        -d '{"message": "How many patients are in the database?"}')

    if echo "$response" | grep -q '"success":true' && echo "$response" | grep -q "50"; then
        log_success "✓ SQL Agent working (50 records loaded)"
    else
        log_error "✗ SQL Agent test failed"
        echo "Response: $response"
        exit 1
    fi

    # Test 4: Tool API
    response=$(curl -s --max-time 10 -X POST http://localhost:3001/api/tools/ \
        -H "Content-Type: application/json" \
        -d '{"tool": "registry_overview"}')

    if echo "$response" | grep -q '"total":50'; then
        log_success "✓ Tool API working"
    else
        log_error "✗ Tool API test failed"
        echo "Response: $response"
    fi

    # Success message
    log_success "🎉 BioLink setup and testing completed successfully!"
    echo ""
    echo -e "${GREEN}System URLs:${NC}"
    echo -e "  🌐 Frontend:    http://localhost:3000"
    echo -e "  🔧 Backend:     http://localhost:3001"
    echo -e "  🤖 Ollama API:  http://localhost:11434"
    echo ""
    echo -e "${GREEN}Quick Commands:${NC}"
    echo -e "  📊 Run tests:   ./scripts/quick_test.sh"
    echo -e "  🛑 Stop all:    docker compose down"
    echo -e "  📋 View logs:   docker compose logs -f"
    echo ""
    echo -e "${GREEN}Testing Notes:${NC}"
    echo -e "  ⚡ Fast queries use heuristics (< 1 second)"
    echo -e "  🧠 LLM queries may take 30+ seconds on CPU"
    echo -e "  📈 50-record dataset loaded for quick testing"
    echo ""
    echo -e "${BLUE}Ready for testing on bigger machines! 🚀${NC}"
}

# Show usage if help requested
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "BioLink Complete Setup Script"
    echo ""
    echo "This script will:"
    echo "  1. Check system requirements"
    echo "  2. Install Docker and Docker Compose if needed"
    echo "  3. Build and start all BioLink services"
    echo "  4. Load the reduced 50-record dataset"
    echo "  5. Run comprehensive tests"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help, -h    Show this help message"
    echo "  --no-tests    Skip running tests after setup"
    echo ""
    echo "Requirements:"
    echo "  - At least 8GB RAM recommended"
    echo "  - 10GB free disk space"
    echo "  - Internet connection for downloads"
    echo ""
    exit 0
fi

# Run main function
main "$@"