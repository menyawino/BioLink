# BioLink Non-Docker Installation

This script provides an alternative installation method for BioLink that doesn't require Docker. It installs all dependencies natively on macOS using Homebrew and on Linux using apt.

## Prerequisites

- macOS or Linux (Ubuntu/Debian recommended)
- At least 8GB RAM recommended
- At least 10GB free disk space
- Internet connection for downloading dependencies

## Quick Start

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/menyawino/BioLink.git
   cd BioLink/
   ```

2. **Run the installation script**:
   ```bash
   ./install-nondocker.sh install
   ```

   This will:
   - Install Homebrew (if not present)
   - Install PostgreSQL, Kafka, Ollama, Python 3.11, Node.js
   - Setup databases and extensions
   - Install Python and Node.js dependencies
   - Setup Ollama models
   - Load initial data

3. **Start the application**:
   ```bash
   ./install-nondocker.sh start
   ```

4. **Open in browser**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:3001
   - API Docs: http://localhost:3001/docs

## Script Commands

- `./install-nondocker.sh install` - Full installation and setup
- `./install-nondocker.sh start` - Start all services and application
- `./install-nondocker.sh stop` - Stop the application
- `./install-nondocker.sh status` - Check status of all services
- `./install-nondocker.sh restart` - Restart everything

## What Gets Installed

### System Packages (via Homebrew)
- PostgreSQL 16 with pgvector extension
- Apache Kafka with Zookeeper
- Ollama (AI model server)
- Python 3.11
- Node.js

### Python Dependencies
- FastAPI, Uvicorn
- SQLAlchemy, Pydantic
- LangChain, LangGraph
- pgvector, kafka-python
- pandas, matplotlib, plotly

### Node.js Dependencies
- React, TypeScript
- Vite
- Radix UI components
- Chart libraries (ECharts, Recharts)

## Services Started

- PostgreSQL databases: `biolink` and `biolink_vector`
- Kafka broker on port 9092 (with Zookeeper)
- Ollama server on port 11434
- Backend API on port 3001
- Frontend dev server on port 5173

## Linux Installation Details

On Linux systems, the script:
- Downloads Apache Kafka directly from official Apache mirrors
- Creates dedicated `kafka` user and proper directory structure
- Sets up systemd services for Zookeeper and Kafka (when available)
- Falls back to manual process management in environments without systemd (WSL, containers)
- Configures Kafka for single-node operation
- Enables services to start automatically on boot (when systemd is available)

This provides a robust Kafka installation that works in various Linux environments including native installations, WSL, and containers.

## Configuration

The script automatically copies `backend-py/.env.example` to `backend-py/.env`. You may need to adjust database connection settings if you have custom PostgreSQL configurations.

## Troubleshooting

### Check Service Status
```bash
./install-nondocker.sh status
```

### View Logs
- Backend logs: `backend-py/backend.log`
- Frontend logs: `frontend.log`

### Manual Service Management
```bash
# PostgreSQL
brew services start postgresql@16
brew services stop postgresql@16

# Kafka
brew services start zookeeper
brew services start kafka

# Ollama
brew services start ollama
```

### Reset Everything
If you need to start fresh:
```bash
./install-nondocker.sh stop
# Remove databases and reinstall
dropdb biolink
dropdb biolink_vector
./install-nondocker.sh install
```

## Limitations vs Docker Setup

- No SQL Server support (uses PostgreSQL only)
- No Debezium CDC (Kafka is installed but not configured for CDC)
- Manual service management required
- Less isolated environment (services run system-wide)

## Migration from Docker

If you have existing Docker containers with data:

1. Export your data from Docker containers
2. Stop Docker containers
3. Run this non-Docker installation
4. Import your data into the native PostgreSQL databases

See [MIGRATION.md](MIGRATION.md) for detailed migration instructions.