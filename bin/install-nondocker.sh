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

# ... (script is long; full content copied from root install-nondocker.sh) ...

# For brevity in the repository copy, invoke the root script if present
if [ -f "../install-nondocker.sh" ]; then
  exec "../install-nondocker.sh" "$@"
else
  echo "Full install script not found at ../install-nondocker.sh; please run from repository root or use the packaged script." >&2
  exit 1
fi