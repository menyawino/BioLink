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

    A1 --> S1
    A2 --> S1

    subgraph Stage1[Stage 1: De-identify + Reduce]
      S1[step_1_remove_pii.py\nstep_2_reduce_sparse_columns.py]
    end

    S1 --> S2
    subgraph Stage2[Stage 2: Profile + Clean]
      S2[step_3_profile_normalization.py\nstep_4_apply_range_rules.py]
    end

    S2 --> S3
    subgraph Stage3[Stage 3: Units + Standardization]
      S3[step_5_extract_units.py\nstep_6_fuzzy_match_v2.py]
    end

    S3 --> S4
    subgraph Stage4[Stage 4: Unify + Publish]
      S4[step_7_unify_datasets.py]
      R[(outputs/unified_registry.csv)]
      A[(outputs/comparability_report.json)]
      Q[(outputs/data_quality_report.html)]
      C[(outputs/cohort_characterization.csv)]
      S4 --> R
      S4 --> A
      S4 --> Q
      S4 --> C
    end

    style S1 fill:#e6f6fc,stroke:#00a2dd,stroke-width:2px
    style S2 fill:#e6f6fc,stroke:#00a2dd,stroke-width:2px
    style S3 fill:#e6f6fc,stroke:#00a2dd,stroke-width:2px
    style S4 fill:#e6f6fc,stroke:#00a2dd,stroke-width:2px
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
