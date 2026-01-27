# MYF BioLink - AI-Powered Cardiovascular Research Registry

> **🤖 Now with Natural Language AI Agent - Control everything through chat!**

A comprehensive web-based platform for managing and analyzing cardiovascular research data from the Magdi Yacoub Heart Foundation's EHVol Registry. Built with React, TypeScript, PostgreSQL, and AI-powered chat agents.

## 🚀 Quick Start (Automated Setup)

For the fastest setup on any machine with internet access:

```bash
# Clone the repository
git clone https://github.com/menyawino/BioLink.git
cd BioLink/

# Run the complete setup script (first time)
./setup-and-test.sh

# Or just run if already set up
./run.sh
```

These scripts will:
- ✅ Check system requirements (8GB RAM, 10GB disk)
- ✅ Install Docker and Docker Compose if needed
- ✅ **Automatically detect and configure GPU acceleration** (NVIDIA/Apple Silicon/AMD)
- ✅ Build and start all services
- ✅ Load reduced 50-record dataset for testing
- ✅ Run comprehensive tests
- ✅ Open frontend in browser
- ✅ Provide access URLs

**Migration to bigger machines**: Just copy the project and run `./setup-and-test.sh`!

📋 **[Complete Migration Guide →](MIGRATION.md)**

## 🌟 NEW: AI Agent System

BioLink now features a **complete agentic system** powered by AI with function calling. Interact with the entire platform using natural language:

```
"How many patients have diabetes?"
"Build a cohort of male patients over 60 with hypertension"
"Show me the age distribution"
"Take me to the analytics dashboard"
"Find patient EHV001 and show their details"
```

**✅ Fully Functional** - The agent can search, filter, analyze, navigate, and control every aspect of the platform.

📖 **[Read the complete AI Agent documentation →](AGENT_SYSTEM.md)**  
⚡ **[Quick reference guide →](QUICK_REFERENCE.md)**

## 📋 Available Scripts

- **`./setup-and-test.sh`**: Complete first-time setup with system checks, dependency installation, and testing
- **`./run.sh`**: Quick start for machines that already have the environment set up
- **`./scripts/start-all.sh`**: Start all Docker services (assumes Docker is running)
- **`./scripts/quick_test.sh`**: Run basic functionality tests against running services

---

## Overview

MYF BioLink is a sophisticated registry management system that provides:
- **Patient Registry Management**: Browse, search, and filter 669+ patient records
- **Advanced Cohort Builder**: Multi-dimensional patient selection with clinical, demographic, temporal, and geographic filters
- **Interactive Analytics**: Comprehensive data visualization and insights
- **Chart Builder**: Custom visualization creation for research analysis
- **Data Dictionary**: Complete metadata and variable documentation
- **Individual Patient Profiles**: Detailed clinical, imaging, and genomic data views

## Architecture

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Components**: shadcn/ui with Radix UI primitives
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **State Management**: Custom React hooks with API integration

### Backend
- **Runtime**: Python (FastAPI)
- **Database**: PostgreSQL
- **ORM/DB**: SQLAlchemy
- **Development**: Uvicorn with hot reload

### MCP (Local Tooling)
- **Server**: Node.js MCP server in mcp/server.mjs
- **Data**: PostgreSQL via DATABASE_URL
- **Charts**: Vega-Lite specs returned from tools

### Database Schema (Streamlined)
- `patients`: Single denormalized source of truth
- `patient_summary`: View used by list/search/analytics/charts

The backend auto-bootstraps these objects at startup.

## Getting Started

### Prerequisites

#### System Requirements
- **RAM**: 8GB minimum (16GB recommended)
- **Disk Space**: 10GB free
- **OS**: macOS, Linux, or Windows with WSL2
- **Docker**: Will be installed automatically by the setup script

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd BioLink/Code
```

2. **Configure environment**

Create env files from the examples:
```env
# frontend
VITE_BACKEND_URL=http://localhost:3001

# backend
DATABASE_URL=postgresql://user:password@localhost:5432/biolink
PORT=3001
ENVIRONMENT=development
```

📖 **See [AGENT_SYSTEM.md](AGENT_SYSTEM.md) for complete AI agent setup and usage**

### Fast Docker-First Install (Recommended)

Use this order to ensure Docker components are ready before tests:

1. **Install and verify Docker components**
```bash
./setup-and-test.sh
```

If Docker is already installed, you can skip the full script and do:

2. **Start the full stack**
```bash
docker compose up -d --build
```

3. **Run tests after services are healthy**
```bash
./scripts/quick_test.sh
python -m unittest discover -s backend-py/tests
```

If you prefer a single command, run the full setup script from Quick Start.

3. **Load data (optional)**

If you have the standardized CSV available under `db/`, import it:

```bash
cd backend-py
python -m app.scripts.import_patients_csv
```

### Running the Application (Docker)

**Start the full stack (frontend, backend, SQL Server, pgvector, Kafka, Debezium, Ollama):**
```bash
docker compose up -d --build
```

Frontend: http://localhost:3000
Backend: http://localhost:3001
Ollama: http://localhost:11434

**Stop the stack:**
```bash
docker compose down
```

### MCP Tools (SQL + Charts)

An MCP server is included to let your local model call tools that query SQL and generate chart specs.

Config: .mcphost.json

Tools exposed:
- query_sql
- search_patients
- get_patient_details
- build_cohort
- registry_overview
- demographics
- enrollment_trends
- data_intersections
- chart_from_sql

The MCP server reads DATABASE_URL from backend-py/.env.

---

## RAG Pipeline (SQL Server → pgvector → Ollama)

Live semantic search over EHVol notes/diagnoses, synced from SQL Server into pgvector.

Quick start:

```bash
docker compose -f docker-compose.rag.yml up -d
cd backend-py
python -m app.scripts.sqlserver_smoke_test
python -m app.scripts.stage2_pgvector_setup
python -m app.scripts.stage3_embed_sample
python -m app.scripts.stage5_rag_query
```

API:
- `POST /api/rag` → `{ "question": "..." }`

## Features

### 1. Patient Registry
- **Search & Filter**: Search by DNA ID, nationality, city
- **Advanced Filtering**: Filter by gender, age range, data completeness
- **Sortable Columns**: Sort by any field (age, enrollment date, completeness, etc.)
- **Data Export**: Export selected patients to CSV
- **Pagination**: Efficient browsing of large datasets
- **Quick Actions**: View individual patient profiles with one click

### 2. Cohort Builder
Multi-dimensional patient selection with:
- **Demographics**: Age range, gender, ethnicity filters
- **Clinical**: Diagnoses, risk factors, biomarker ranges
- **Temporal**: Enrollment period, follow-up duration
- **Data Availability**: Required data types, minimum completeness threshold
- **Geographic**: Region and site selection
- **Real-time Estimation**: Live patient count as filters are applied
- **Export Options**: CSV and JSON export with full criteria metadata

### 3. Registry Analytics
Comprehensive analytics dashboard with:
- **Demographics Analysis**: Age/gender distribution, nationality breakdown
- **Data Quality Metrics**: Completeness by category, data availability
- **Clinical Metrics**: BMI distribution, blood pressure, EF measurements
- **Geographic Mapping**: Patient distribution by region
- **Enrollment Trends**: Patient recruitment over time
- **Timeline Explorer**: Longitudinal data visualization

### 4. Chart Builder
Interactive chart creation tool:
- **Multiple Chart Types**: Bar, line, scatter, pie charts
- **Flexible Axis Selection**: Choose from 60+ available fields
- **Category Grouping**: Group data by demographics or clinical factors
- **Real-time Preview**: Instant visualization updates
- **Export Options**: Save charts as images or data

### 5. Data Dictionary
Complete variable documentation:
- **10 Data Categories**: Demographics, Clinical, Imaging, Labs, Lifestyle, etc.
- **60+ Variables**: Full metadata for all database fields
- **Statistics**: Available count and completeness for each field
- **Descriptions**: Clinical definitions and units
- **Data Types**: Field types and validation rules

## 🔧 API Endpoints

### Patient Endpoints
```
GET  /api/patients              - List patients with pagination and filters
GET  /api/patients/:dnaId       - Get single patient details
GET  /api/patients/:dnaId/vitals - Get patient vital signs
GET  /api/patients/:dnaId/imaging - Get imaging data (Echo + MRI)
GET  /api/patients/search/:query - Search patients
```

### Analytics Endpoints
```
GET  /api/analytics/overview        - Registry overview statistics
GET  /api/analytics/demographics    - Demographics breakdown
GET  /api/analytics/clinical        - Clinical metrics distribution
GET  /api/analytics/comorbidities   - Comorbidity analysis
GET  /api/analytics/lifestyle       - Lifestyle statistics
GET  /api/analytics/geographic      - Geographic distribution
GET  /api/analytics/data-quality    - Data quality metrics
GET  /api/analytics/imaging         - Imaging statistics
```

### Chart Data Endpoint
```
GET  /api/charts/data              - Get aggregated chart data
```

## UI Components

Built with shadcn/ui and Radix UI:
- `Button`, `Input`, `Select`, `Checkbox`, `Slider`
- `Card`, `Badge`, `Alert`, `Dialog`, `Sheet`
- `Table`, `Tabs`, `Accordion`, `Popover`
- `Chart` (Recharts integration)
- Custom `Sidebar`, `PatientHeader` components

## 📁 Project Structure

```
BioLink/Code/
├── src/
│   ├── components/        # React components
│   │   ├── ui/           # shadcn/ui components
│   │   ├── CohortBuilder.tsx
│   │   ├── PatientRegistryTable.tsx
│   │   ├── RegistryAnalytics.tsx
│   │   ├── ChartBuilder.tsx
│   │   └── ...
│   ├── api/              # API client functions
│   ├── hooks/            # Custom React hooks
│   ├── styles/           # Global styles
│   ├── App.tsx           # Main application component
│   └── main.tsx          # Application entry point
├── backend/
│   ├── src/
│   │   ├── routes/       # API route handlers
│   │   ├── db/           # Database connection
│   │   └── index.ts      # Server entry point
│   └── package.json
├── db/                   # Database files and scripts
├── build/                # Production build output
└── package.json
```

## Technology Stack:

- **React 18**: Modern React with hooks and concurrent features
- **TypeScript**: Type-safe development
- **Vite**: Fast build tooling and HMR
- **Tailwind CSS**: Utility-first styling
- **Hono**: Lightweight web framework for Node.js
- **PostgreSQL**: Robust relational database
- **Recharts**: Composable charting library
- **Radix UI**: Accessible component primitives

## Troubleshooting

### Backend Issues
- Ensure PostgreSQL is running: `pg_isready`
- Check database connection in backend logs
- Verify environment variables in `.env`

### Frontend Issues
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`
- Check port 3000 is not in use

### Database Issues
- Check table schemas match expected structure
- Verify foreign key relationships
- Ensure proper permissions for database user

## Development

### Building for Production
```bash
# Build frontend
npm run build

# Build backend
cd backend
npm run build
```

### Code Quality
- TypeScript strict mode enabled
- ESLint configuration for code standards
- Type checking: `npx tsc --noEmit`
