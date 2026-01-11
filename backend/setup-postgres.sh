#!/bin/bash
# PostgreSQL Setup Script for Conda Environment
# Run this script to set up PostgreSQL without Docker

set -e

PGDATA="$(pwd)/pgdata"
PGPORT=5432
DB_NAME="biolink"
DB_USER="biolink"
DB_PASSWORD="biolink_secret"

echo "🐘 Setting up PostgreSQL with Conda..."

# Check if PostgreSQL is installed
if ! command -v pg_ctl &> /dev/null; then
    echo "📦 Installing PostgreSQL via conda..."
    mamba install -y postgresql || conda install -y postgresql
fi

# Initialize database if not exists
if [ ! -d "$PGDATA" ]; then
    echo "📁 Initializing PostgreSQL data directory..."
    initdb -D "$PGDATA" -U postgres
fi

# Update pg_hba.conf to allow password authentication
cat > "$PGDATA/pg_hba.conf" << EOF
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
EOF

# Start PostgreSQL server
echo "🚀 Starting PostgreSQL server..."
pg_ctl -D "$PGDATA" -l "$PGDATA/logfile" -o "-p $PGPORT" start || true

# Wait for PostgreSQL to be ready
sleep 2

# Create user and database
echo "👤 Creating database and user..."
psql -U postgres -p $PGPORT << EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE ROLE $DB_USER WITH LOGIN PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

# Run schema
echo "📋 Running database schema..."
PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -p $PGPORT -f init/01_schema.sql

echo "✅ PostgreSQL setup complete!"
echo ""
echo "Connection details:"
echo "  Host: localhost"
echo "  Port: $PGPORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo ""
echo "To import data, run: npm run import-data"
echo "To start the API server, run: npm run dev"
echo ""
echo "To stop PostgreSQL later: pg_ctl -D $PGDATA stop"
echo "To start PostgreSQL later: pg_ctl -D $PGDATA -l $PGDATA/logfile start"
