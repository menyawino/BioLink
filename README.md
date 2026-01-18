# MYF BioLink - AI-Powered Cardiovascular Research Registry

> **🤖 Now with Natural Language AI Agent - Control everything through chat!**

A comprehensive web-based platform for managing and analyzing cardiovascular research data from the Magdi Yacoub Heart Foundation's EHVol Registry. Built with React, TypeScript, PostgreSQL, and Azure OpenAI.

## 🌟 NEW: AI Agent System

BioLink now features a **complete agentic system** powered by Azure OpenAI with function calling. Interact with the entire platform using natural language:

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

### Database Schema (Streamlined)
- `patients`: Single denormalized source of truth
- `patient_summary`: View used by list/search/analytics/charts

The backend auto-bootstraps these objects at startup.

## Getting Started

### Prerequisites
- Node.js 18+ 
- PostgreSQL 14+
- Mamba/Conda (optional, for gcloud environment)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd BioLink/Code
```

2. **Install frontend dependencies**
```bash
npm install
```

3. **Install backend dependencies**
```bash
cd backend-py
pip install -r requirements.txt
```

4. **Configure environment**

Create env files from the examples:
```env
# frontend
VITE_API_URL=http://localhost:3001

# backend
DATABASE_URL=postgresql://user:password@localhost:5432/biolink
PORT=3001
ENVIRONMENT=development
```

📖 **See [AGENT_SYSTEM.md](AGENT_SYSTEM.md) for complete AI agent setup and usage**

5. **Load data (optional)**

If you have the standardized CSV available under `db/`, import it:

```bash
cd backend-py
python -m app.scripts.import_patients_csv
```

### Running the Application

#### Option 1: Standard Node.js

(Legacy docs removed — backend is Python now.)

**Start the frontend dev server:**
```bash
npm run dev
```
Frontend runs at: http://localhost:3000

#### Option 2: With Conda/Mamba Environment

**Backend:**
```bash
mamba activate gcloud
cd backend-py
./start.sh
```

**Frontend:**
```bash
mamba activate gcloud
npm run dev
```

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