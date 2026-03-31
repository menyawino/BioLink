import React, { useState } from 'react';
import { MermaidChart } from './MermaidChart';
import { Network, Database, Workflow, ShieldCheck } from 'lucide-react';

const charts = [
  {
    id: 'ecosystem',
    name: 'Clinical Harmonization Ecosystem',
    icon: <Network className="w-5 h-5" />,
    chart: `
flowchart TD
    A[Clinical Data Sources\\nBHS, EHVol, New Cohorts] --> B[Data Preprocessing\\nCleaning, Normalization, De-identification]
    B --> C[Harmonization Methods\\nRule-based + Semantic ML + Validation]
    C --> D[Interoperability Standards\\nOMOP, FHIR, openEHR, CDISC]
    D --> E[Research Applications\\nRisk Models, Multi-cohort Studies, CDS]

    style A fill:#f5f5f5,stroke:#717182,stroke-width:2px
    style B fill:#e6f6fc,stroke:#00a2dd,stroke-width:2px
    style C fill:#fdf4df,stroke:#efb01b,stroke-width:2px
    style D fill:#f1f9fd,stroke:#0084b6,stroke-width:2px
    style E fill:#f5f5f5,stroke:#717182,stroke-width:2px
`
  },
  {
    id: 'etl',
    name: 'Implemented 4-Stage Pipeline',
    icon: <Database className="w-5 h-5" />,
    chart: `
flowchart LR
    subgraph Source
        A1[BHS_Full.csv]
        A2[EHVol_Full.csv]
    end

    A1 --> P
    A2 --> P

    subgraph Stage1[Stage 1: Profile + Match]
        P[two_stage_match.py]
        M[(master_schema.csv)]
        P --> M
    end

    M --> S
    subgraph Stage2[Stage 2: Apply Schema + PII Scrub]
        S[apply_schema.py]
        U[(unified_registry.csv)]
        S --> U
    end

    U --> O
    subgraph Stage3[Stage 3: OMOP Bootstrap]
        O[omop_etl.py]
        C[(outputs/omop_cdm)]
        O --> C
    end

    C --> Q
    subgraph Stage4[Stage 4: Quality + Characterization]
        Q[omop_quality.py]
        R[data_quality_report.html + cohort_characterization.csv]
        Q --> R
    end

    style P fill:#e6f6fc,stroke:#00a2dd,stroke-width:2px
    style S fill:#e6f6fc,stroke:#00a2dd,stroke-width:2px
    style O fill:#e6f6fc,stroke:#00a2dd,stroke-width:2px
    style Q fill:#e6f6fc,stroke:#00a2dd,stroke-width:2px
`
  },
  {
    id: 'evolution',
    name: 'Harmonization Method Evolution',
    icon: <Workflow className="w-5 h-5" />,
    chart: `
graph LR
    A[Manual Dictionaries\\nLow automation] --> B[String Similarity\\nBasic automation]
    B --> C[Ontology and Terminology Mapping\\nHigher semantic quality]
    C --> D[Transformer Semantic Matching\\nHigh automation]
    D --> E[Hybrid Semantic Pipelines\\nHigh automation + high reliability]

    style A fill:#f5f5f5,stroke:#717182,stroke-width:2px
    style B fill:#f5f5f5,stroke:#717182,stroke-width:2px
    style C fill:#fdf4df,stroke:#efb01b,stroke-width:2px
    style D fill:#e6f6fc,stroke:#00a2dd,stroke-width:2px
    style E fill:#f1f9fd,stroke:#0084b6,stroke-width:3px
`
  },
  {
    id: 'criteria',
    name: 'Design Criteria for Program Governance',
    icon: <ShieldCheck className="w-5 h-5" />,
    chart: `
flowchart TB
    A[Governance Targets] --> B[Mapping accuracy > 85%]
    A --> C[Variable coverage > 80%]
    A --> D[Manual mapping < 20%]
    A --> E[Cohort onboarding < 1 week]
    A --> F[Privacy and provenance controls]

    style A fill:#f1f9fd,stroke:#0084b6,stroke-width:2px
    style B fill:#e6f6fc,stroke:#00a2dd,stroke-width:2px
    style C fill:#e6f6fc,stroke:#00a2dd,stroke-width:2px
    style D fill:#e6f6fc,stroke:#00a2dd,stroke-width:2px
    style E fill:#e6f6fc,stroke:#00a2dd,stroke-width:2px
    style F fill:#fdf4df,stroke:#efb01b,stroke-width:2px
`
  }
];

export function SystemArchitectureCharts() {
  const [activeTab, setActiveTab] = useState(charts[0].id);
  
  const currentChart = charts.find(c => c.id === activeTab) || charts[0];

  return (
    <div className="system-architecture-charts mt-12 mb-8 col-span-full w-full">
      <div className="flex flex-wrap gap-3 mb-6 justify-center">
        {charts.map((chart) => (
          <button
            key={chart.id}
            onClick={() => setActiveTab(chart.id)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-full font-semibold transition-all duration-200 ${
              activeTab === chart.id 
                ? 'bg-[var(--primary)] text-white shadow-md transform scale-105' 
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200 hover:shadow-sm'
            }`}
          >
            {chart.icon}
            <span>{chart.name}</span>
          </button>
        ))}
      </div>
      
      <div className="bg-slate-50/80 p-4 md:p-8 rounded-2xl border border-slate-200 shadow-inner">
        <div className="mb-6 text-center">
            <h3 className="text-2xl font-bold tracking-tight text-slate-800">{currentChart.name}</h3>
            <p className="text-slate-500 mt-2 text-sm">Interactive Architecture Diagram</p>
        </div>
        <MermaidChart chart={currentChart.chart} name={currentChart.id} />
      </div>
    </div>
  );
}
