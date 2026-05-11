import { useEffect, useMemo, useRef, useState } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  ArrowRight,
  BarChart3,
  BookOpen,
  Boxes,
  Brain,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Database,
  FileBarChart,
  GitBranch,
  HardDrive,
  LockKeyhole,
  MessageSquare,
  Microscope,
  Network,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
  Waypoints,
  Workflow,
} from "lucide-react";
import logo from "figma:asset/e26cb8b78ee049387f524876448562f480bca21b.png";
import { SystemArchitectureCharts } from "./components/SystemArchitectureCharts";
import "./charts-tailwind.css";

interface Pillar {
  label: string;
  title: string;
  description: string;
}

interface Capability {
  label: string;
  title: string;
  description: string;
  icon: LucideIcon;
  bullets: string[];
}

interface ArchitectureLane {
  title: string;
  description: string;
  icon: LucideIcon;
  chips: string[];
}

interface TimelineStep {
  step: string;
  title: string;
  description: string;
  outputs: string[];
}

interface OpsCard {
  title: string;
  description: string;
  icon: LucideIcon;
}

interface SnapshotStat {
  label: string;
  value: string;
  detail: string;
}

interface NarrativeCard {
  title: string;
  description: string;
  icon: LucideIcon;
}

interface ProductScreen {
  title: string;
  description: string;
  src: string;
  alt: string;
  tags: string[];
  highlights: string[];
  frame: "landscape" | "portrait";
}

interface SlideMeta {
  id: string;
  label: string;
  title: string;
  nav: string;
}

const pillars: Pillar[] = [
  {
    label: "01",
    title: "Structural heterogeneity",
    description: "The two source registries differ sharply in schema width and naming conventions, so direct pooling is not reliable.",
  },
  {
    label: "02",
    title: "Semantic heterogeneity",
    description: "Equivalent clinical concepts appear under different labels and formats, requiring semantic matching instead of string matching alone.",
  },
  {
    label: "03",
    title: "Representation heterogeneity",
    description: "Units, categorical encodings, and date patterns vary by cohort, creating analysis risk without normalization.",
  },
  {
    label: "04",
    title: "Governance and quality",
    description: "PII controls, provenance tracking, and quality reporting are mandatory for trustworthy multi-cohort cardiovascular studies.",
  },
];

const capabilities: Capability[] = [
  {
    label: "Family 1",
    title: "Rule-based harmonization",
    description: "Manual dictionaries and deterministic transforms remain important for clinical transparency and auditability.",
    icon: BookOpen,
    bullets: ["Column dictionaries and regex transforms", "Typed normalization (gender, boolean, date, numeric)", "Clinically interpretable and auditable"],
  },
  {
    label: "Family 2",
    title: "Statistical schema matching",
    description: "Lexical and structural similarity methods automate candidate generation but can fail on true clinical semantics.",
    icon: BarChart3,
    bullets: ["String similarity and n-gram methods", "Useful for candidate narrowing", "Insufficient alone for clinical safety"],
  },
  {
    label: "Family 3",
    title: "Semantic ML mapping",
    description: "This codebase now standardizes cohorts through the db/test preparation flow, combining profiling, range rules, unit extraction, and fuzzy canonicalization.",
    icon: Brain,
    bullets: ["Normalization profiling by observed values", "Range cleaning and outlier quarantine", "Geographic and nationality canonicalization"],
  },
  {
    label: "Family 4",
    title: "Hybrid semantic validation",
    description: "The implemented pipeline blends deterministic cleaning, typed normalization cues, and unification rules across cohorts.",
    icon: Sparkles,
    bullets: ["PII removal and sparse-column reduction", "Range and unit standardization passes", "Cross-dataset unification with modality awareness"],
  },
  {
    label: "Quality",
    title: "Data quality + characterization",
    description: "Quality artifacts are produced directly from the unified db/test outputs to quantify completeness, comparability, and cohort profile signals.",
    icon: FileBarChart,
    bullets: ["data_quality_report.html", "cohort_characterization.csv", "comparability_report.json and characterization_metrics.csv"],
  },
  {
    label: "Governance",
    title: "Transparent unification outputs",
    description: "The new pipeline publishes explicit mapping, value-set, unit, and modality outputs instead of hidden transformation state.",
    icon: LockKeyhole,
    bullets: ["step_7/column_mapping.csv", "step_7/value_set_mapping.csv", "step_7/unit_mapping.csv and modality_manifest.csv"],
  },
  {
    label: "Operations",
    title: "Pipeline orchestration",
    description: "NiFi-backed orchestration and ETL APIs convert harmonization from ad-hoc scripts into an operational process.",
    icon: Workflow,
    bullets: ["NiFi processor-triggered ETL", "Script-aligned stages documented in docs", "UI ETL monitor for visibility"],
  },
];

const architecture: ArchitectureLane[] = [
  {
    title: "Clinical data sources",
    description: "Current baseline ingestion starts from BHS and EHVol registries, with architecture designed to onboard additional cohorts.",
    icon: HardDrive,
    chips: ["BHS_Full.csv", "EHVol_Full.csv", "Future cohorts", "Heterogeneous schemas"],
  },
  {
    title: "Preprocessing and profiling",
    description: "Cohort profiling, sparse-column reduction, range rules, and unit extraction prepare the data for cross-dataset unification.",
    icon: RefreshCw,
    chips: ["step_1_remove_pii.py", "step_2_reduce_sparse_columns.py", "step_4_apply_range_rules.py", "step_5_extract_units.py"],
  },
  {
    title: "Harmonization methods",
    description: "Unification combines canonical concept naming, modality tagging, value harmonization, and accepted fuzzy mappings for safer pooling.",
    icon: Brain,
    chips: ["normalize_concept_name", "modality detection", "value set rules", "step_6 fuzzy suggestions"],
  },
  {
    title: "Standards and research outputs",
    description: "The harmonized registry now publishes a unified wide table and explicit audit outputs for downstream analysis and governance.",
    icon: Network,
    chips: ["unified_wide_table.csv", "column_mapping.csv", "comparability_report.json", "cohort_characterization.csv"],
  },
];

const timeline: TimelineStep[] = [
  {
    step: "01",
    title: "De-identify and reduce",
    description: "Incoming registry files are de-identified, reduced for sparsity, and validated for structural quality before pooling.",
    outputs: ["step_1_remove_pii.py", "step_2_reduce_sparse_columns.py", "Validation audits"],
  },
  {
    step: "02",
    title: "Profile values and clean ranges",
    description: "Normalization profiling and range-rule passes identify safe conversions and quarantine implausible clinical values.",
    outputs: ["step_3_profile_normalization.py", "step_4_apply_range_rules.py", "Range audits"],
  },
  {
    step: "03",
    title: "Extract units and standardize geography",
    description: "Unit extraction and fuzzy canonicalization reduce representation drift across text, geography, and nationality fields.",
    outputs: ["step_5_extract_units.py", "step_6_fuzzy_match_v2.py", "Canonical suggestions"],
  },
  {
    step: "04",
    title: "Unify and publish audit outputs",
    description: "The final step produces the unified registry snapshot and publishes mapping, modality, comparability, and characterization outputs.",
    outputs: ["step_7_unify_datasets.py", "unified_registry.csv", "comparability_report.json"],
  },
];

const operations: OpsCard[] = [
  {
    title: "Mapping accuracy goal",
    description: "Treat >85% validated mapping precision as a minimum program target before expanding to additional cohorts.",
    icon: ShieldCheck,
  },
  {
    title: "Coverage goal",
    description: "Prioritize >80% variable coverage on core cardiovascular concepts and make uncovered fields explicit in onboarding reports.",
    icon: LockKeyhole,
  },
  {
    title: "Manual effort limit",
    description: "Keep manual mapping below 20% by combining lexicon maintenance, semantic matching, and distribution-aware checks.",
    icon: Activity,
  },
  {
    title: "Cohort onboarding speed",
    description: "Target sub-1-week onboarding for new cohorts using the existing four-stage ETL process and quality gate artifacts.",
    icon: Boxes,
  },
];

const deploymentModes = [
  {
    title: "Decision 1: Approve hybrid strategy",
    description: "Adopt a hybrid harmonization strategy (semantic matching + rule-based controls + quality gates) as the baseline architecture.",
    icon: HardDrive,
  },
  {
    title: "Decision 2: Formalize standards path",
    description: "Continue OMOP bootstrap adoption and define phased terminology governance toward broader interoperability targets.",
    icon: Waypoints,
  },
  {
    title: "Decision 3: Fund cohort onboarding",
    description: "Resource lexicon expansion, clinical review cycles, and QA automation to safely scale beyond the initial two cohorts.",
    icon: GitBranch,
  },
];

const snapshotStats: SnapshotStat[] = [
  {
    label: "Source schema size",
    value: "BHS: 776 cols | EHVol: 168 cols",
    detail: "Direct evidence from db/BHS_Full.csv and db/EHVol_Full.csv headers shows major structural mismatch.",
  },
  {
    label: "Unified registry",
    value: "4,943 harmonized participant rows",
    detail: "outputs/unified_registry.csv consolidates both cohorts after the db/test unification flow.",
  },
  {
    label: "Harmonization scope",
    value: "658 canonical concepts",
    detail: "step_7/unification_audit.json records the current shared and cohort-specific concept coverage across both registries.",
  },
  {
    label: "Quality artifacts",
    value: "Quality + comparability outputs",
    detail: "The pipeline emits unified-registry audit outputs, quality reports, and comparability metrics for governance review.",
  },
];

const narrativeCards: NarrativeCard[] = [
  {
    title: "Why this matters",
    description: "Without harmonization, cross-cohort cardiovascular modeling is error-prone and difficult to audit.",
    icon: Users,
  },
  {
    title: "What is implemented now",
    description: "A four-stage db/test pipeline from de-identification through unification and audit reporting is already running in this repository.",
    icon: Activity,
  },
  {
    title: "What decision is needed",
    description: "Approve the harmonization architecture and governance cadence needed to scale to additional cohorts.",
    icon: Sparkles,
  },
];

const outcomes = [
  "Enable multi-cohort cardiovascular research from currently heterogeneous registries.",
  "Improve reliability of downstream predictive modeling through explicit semantic + quality controls.",
  "Reduce onboarding friction for future cohorts using a repeatable four-stage ETL flow.",
  "Move toward interoperable research assets through OMOP-oriented exports and governed metadata.",
];

const benchmarkCards: OpsCard[] = [
  {
    title: "Manual mapping",
    description: "High transparency but low scalability; best for initial bootstrap and clinically sensitive fields.",
    icon: BookOpen,
  },
  {
    title: "String similarity only",
    description: "Fast candidate generation but weak semantic robustness; should be used as a helper, not a final decision engine.",
    icon: Search,
  },
  {
    title: "Semantic transformer models",
    description: "Improves concept-level matching in biomedical language; this repository uses SapBERT for this stage.",
    icon: Brain,
  },
  {
    title: "Hybrid semantic pipelines",
    description: "Best practical balance: semantic similarity plus rule vetoes, type checks, and distribution validation.",
    icon: Sparkles,
  },
];

const networkCards: OpsCard[] = [
  {
    title: "OHDSI network",
    description: "OMOP-based observational analytics ecosystem and tooling model for multi-institution studies.",
    icon: Database,
  },
  {
    title: "All of Us",
    description: "OMOP-oriented architecture at national scale demonstrates standardization value for cohort science.",
    icon: Users,
  },
  {
    title: "European health pilots",
    description: "FHIR-centered interoperability initiatives illustrate standards-driven exchange patterns.",
    icon: Network,
  },
  {
    title: "Implication for BioLink",
    description: "Continue OMOP-aligned harmonization while keeping terminology governance and quality reporting central.",
    icon: CheckCircle2,
  },
];

const productScreens: ProductScreen[] = [
  {
    title: "Executive framing and decision narrative",
    description: "The hero and opening panel summarize the harmonization problem, implemented baseline, and the specific governance decision needed from stakeholders.",
    src: "/stakeholders/stakeholder-hero.png",
    alt: "Stakeholder site hero and executive snapshot",
    tags: ["Decision framing", "Executive snapshot", "Governance prompt"],
    highlights: ["Problem and decision paired side-by-side", "Pipeline baseline explained in plain language", "Audience-aware executive layout"],
    frame: "landscape",
  },
  {
    title: "Architecture and method visualization",
    description: "This section connects method families to interactive diagrams so non-technical leaders can inspect implementation logic before approving scale-up.",
    src: "/stakeholders/stakeholder-architecture.png",
    alt: "Stakeholder site architecture section with harmonization cards and diagram tabs",
    tags: ["Method families", "Interactive diagrams", "Standards alignment"],
    highlights: ["Cards map directly to method layers", "Mermaid diagrams make flow explicit", "Supports architecture review conversations"],
    frame: "landscape",
  },
  {
    title: "Pipeline proof and operational readiness",
    description: "The proposed four-stage operational path is presented as implemented evidence, linking scripts, artifacts, and quality outputs to decision criteria.",
    src: "/stakeholders/stakeholder-pipeline.png",
    alt: "Stakeholder site pipeline section with four implementation stages",
    tags: ["Script-backed flow", "Artifact outputs", "Operational baseline"],
    highlights: ["Stage cards map to repository scripts", "Outputs are concrete and auditable", "Bridges technical work to board-level decisions"],
    frame: "landscape",
  },
  {
    title: "Visual evidence gallery",
    description: "A dedicated evidence panel demonstrates the live interface captures and strengthens trust that the storyline is grounded in the current implementation.",
    src: "/stakeholders/stakeholder-visuals.png",
    alt: "Stakeholder site visual evidence section with curated screenshots",
    tags: ["Live captures", "Evidence panel", "Traceable narrative"],
    highlights: ["Screenshot evidence supports claims", "Consistent visual language across panels", "Improves stakeholder confidence in readiness"],
    frame: "portrait",
  },
];

const slideDeck: SlideMeta[] = [
  { id: "slide-challenge", label: "Slide 1", title: "The challenge", nav: "Challenge" },
  { id: "slide-problem", label: "Slide 2", title: "The problem", nav: "Problem" },
  { id: "slide-response", label: "Slide 3", title: "How we address it", nav: "Response" },
  { id: "slide-architecture", label: "Slide 4", title: "The architecture", nav: "Architecture" },
  { id: "slide-pipeline", label: "Slide 5", title: "The pipeline", nav: "Pipeline" },
  { id: "slide-benchmark", label: "Slide 6", title: "Benchmark and standards", nav: "Benchmark" },
  { id: "slide-evidence", label: "Slide 7", title: "Visual evidence", nav: "Evidence" },
  { id: "slide-governance", label: "Slide 8", title: "Governance criteria", nav: "Governance" },
  { id: "slide-decision", label: "Slide 9", title: "Decision and next step", nav: "Decision" },
];

function SectionHeading({ eyebrow, title, body }: { eyebrow: string; title: string; body: string }) {
  return (
    <div className="section-heading">
      <span className="eyebrow">{eyebrow}</span>
      <h2>{title}</h2>
      <p>{body}</p>
    </div>
  );
}

export function StakeholderSite() {
  const slides = useMemo(() => slideDeck, []);
  const [activeSlide, setActiveSlide] = useState(0);
  const [showNotes, setShowNotes] = useState(false);
  const activeSlideRef = useRef(0);

  useEffect(() => {
    activeSlideRef.current = activeSlide;
  }, [activeSlide]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const query = new URLSearchParams(window.location.search);
    setShowNotes(query.get("notes") === "1");

    const elements = slides
      .map((slide) => document.getElementById(slide.id))
      .filter((element): element is HTMLElement => element instanceof HTMLElement);

    if (elements.length === 0) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((left, right) => right.intersectionRatio - left.intersectionRatio)[0];

        if (!visible) {
          return;
        }

        const nextIndex = elements.findIndex((element) => element.id === visible.target.id);

        if (nextIndex >= 0) {
          setActiveSlide(nextIndex);
        }
      },
      {
        threshold: [0.35, 0.55, 0.75],
        rootMargin: "-12% 0px -18% 0px",
      },
    );

    elements.forEach((element) => observer.observe(element));

    const goToIndex = (index: number) => {
      const boundedIndex = Math.max(0, Math.min(index, slides.length - 1));
      const target = document.getElementById(slides[boundedIndex].id);

      if (!target) {
        return;
      }

      target.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const isEditable =
        target?.tagName === "INPUT" ||
        target?.tagName === "TEXTAREA" ||
        target?.tagName === "SELECT" ||
        target?.isContentEditable;

      if (isEditable) {
        return;
      }

      if (["ArrowDown", "PageDown"].includes(event.key)) {
        event.preventDefault();
        goToIndex(activeSlideRef.current + 1);
      }

      if (["ArrowUp", "PageUp"].includes(event.key)) {
        event.preventDefault();
        goToIndex(activeSlideRef.current - 1);
      }

      if (event.key === "Home") {
        event.preventDefault();
        goToIndex(0);
      }

      if (event.key === "End") {
        event.preventDefault();
        goToIndex(slides.length - 1);
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      observer.disconnect();
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [slides]);

  const progress = `${((activeSlide + 1) / slides.length) * 100}%`;
  const currentSlide = slides[activeSlide] ?? slides[0];
  const scrollToSlide = (index: number) => {
    if (typeof document === "undefined") {
      return;
    }

    const target = document.getElementById(slides[index]?.id ?? "");

    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <div className={`stakeholder-site stakeholder-deck ${showNotes ? "notes-visible" : ""}`}>
      <div className="backdrop backdrop-one" />
      <div className="backdrop backdrop-two" />

      <div className="slide-progress" aria-hidden="true">
        <span style={{ width: progress }} />
      </div>

      <header className="site-header">
        <a className="brand" href="#top">
          <img src={logo} alt="Magdi Yacoub Heart Foundation" />
          <div>
            <strong>MYF BioLink</strong>
            <span>Stakeholder presentation site</span>
          </div>
        </a>

        <nav className="site-nav" aria-label="Section navigation">
          <a href="#slide-problem">Problem</a>
          <a href="#slide-architecture">Architecture</a>
          <a href="#slide-evidence">Evidence</a>
          <a href="#slide-decision">Decision</a>
        </nav>

        <div className="site-actions">
          <a className="ghost-link" href="/">Open product</a>
          <a className="solid-link" href="#slide-pipeline">
            Review deck
            <ArrowRight size={16} />
          </a>
        </div>
      </header>

      <div className="slide-controls" aria-label="Slide navigation">
        <button type="button" className="slide-nav-button" onClick={() => scrollToSlide(activeSlide - 1)} aria-label="Previous slide">
          <ChevronLeft size={18} />
        </button>
        <div className="slide-dots" role="tablist" aria-label="Slides">
          {slides.map((slide, index) => (
            <button
              key={slide.id}
              type="button"
              role="tab"
              aria-selected={index === activeSlide}
              aria-label={`${slide.label}: ${slide.title}`}
              className={`slide-dot ${index === activeSlide ? "is-active" : ""}`}
              onClick={() => scrollToSlide(index)}
            >
              <span>{slide.nav}</span>
            </button>
          ))}
        </div>
        <button type="button" className="slide-nav-button" onClick={() => scrollToSlide(activeSlide + 1)} aria-label="Next slide">
          <ChevronRight size={18} />
        </button>
      </div>

      <div className="slide-counter">
        <span>{currentSlide.label}</span>
        <strong>
          {activeSlide + 1} / {slides.length}
        </strong>
      </div>

      {showNotes ? (
        <aside className="presenter-notes" aria-label="Presenter notes">
          <strong>Presenter notes</strong>
          <p>Use arrow keys or page up/down to move through the story. Slides 2-5 explain the operating baseline, 6-7 prove readiness, 8-9 concentrate the ask.</p>
        </aside>
      ) : null}

      <main id="top" className="slide-deck-main">
        <section id="slide-challenge" className="slide slide-hero">
          <div className="slide-shell hero-shell panel">
            <div className="slide-heading-block">
              <span className="eyebrow">{slides[0].label}</span>
              <span className="slide-title-chip">{slides[0].title}</span>
            </div>

            <div className="hero-section">
              <div className="hero-copy reveal rise-up">
                <span className="eyebrow">Clinical data harmonization strategy</span>
                <h1>Integrating heterogeneous cardiovascular registries into one analyzable research asset.</h1>
                <p>
                  This deck moves from problem definition to implementation proof, then closes on the governance decision
                  required to scale safely toward multi-cohort cardiovascular research.
                </p>

                <div className="hero-actions">
                  <a className="solid-link" href="#slide-problem">
                    Start story
                    <ChevronRight size={16} />
                  </a>
                  <a className="ghost-link" href="#slide-decision">Skip to ask</a>
                </div>

                <div className="narrative-grid">
                  {narrativeCards.map((item, index) => {
                    const Icon = item.icon;

                    return (
                      <article key={item.title} className="narrative-card" style={{ animationDelay: `${index * 120}ms` }}>
                        <div className="narrative-icon">
                          <Icon size={18} />
                        </div>
                        <div>
                          <h3>{item.title}</h3>
                          <p>{item.description}</p>
                        </div>
                      </article>
                    );
                  })}
                </div>
              </div>

              <div className="hero-board reveal rise-up delayed-one">
                <div className="hero-console">
                  <div className="console-chrome">
                    <span />
                    <span />
                    <span />
                  </div>
                  <div className="console-copy">
                    <span className="panel-kicker">Executive snapshot</span>
                    <h2>From heterogeneous inputs to governed outputs</h2>
                    <p>
                      Current implementation already delivers a script-backed pipeline from schema matching through
                      quality reporting, with explicit provenance and OMOP bootstrap outputs.
                    </p>
                  </div>
                  <div className="hero-route-grid">
                    <div>
                      <strong>Stage 1</strong>
                      <span>Schema profiling and semantic candidate matching</span>
                    </div>
                    <div>
                      <strong>Stage 2</strong>
                      <span>PII-safe schema application and normalization</span>
                    </div>
                    <div>
                      <strong>Stage 3</strong>
                      <span>OMOP bootstrap mapping</span>
                    </div>
                    <div>
                      <strong>Stage 4</strong>
                      <span>Quality and cohort characterization outputs</span>
                    </div>
                  </div>
                </div>

                <div className="hero-grid">
                  <div>
                    <MessageSquare size={18} />
                    <span>Semantic matching + clinical rules</span>
                  </div>
                  <div>
                    <Workflow size={18} />
                    <span>NiFi-triggered ETL orchestration</span>
                  </div>
                  <div>
                    <Microscope size={18} />
                    <span>Heterogeneous cardiovascular registries</span>
                  </div>
                  <div>
                    <FileBarChart size={18} />
                    <span>Quality and comparability reports</span>
                  </div>
                </div>

                <div className="hero-trust-row">
                  <div className="hero-metric-card">
                    <span>Primary objective</span>
                    <strong>Enable unified cardiovascular datasets for cross-cohort analytics and modeling</strong>
                  </div>
                  <div className="hero-metric-card accent-card">
                    <span>Decision focus</span>
                    <strong>Approve harmonization architecture, quality gates, and onboarding investment</strong>
                  </div>
                </div>
              </div>
            </div>

            <div className="snapshot-strip">
              {snapshotStats.map((stat, index) => (
                <article key={stat.label} className="snapshot-card reveal rise-up" style={{ animationDelay: `${index * 90}ms` }}>
                  <span>{stat.label}</span>
                  <strong>{stat.value}</strong>
                  <p>{stat.detail}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="slide-problem" className="slide">
          <div className="slide-shell panel">
            <div className="slide-heading-block">
              <span className="eyebrow">{slides[1].label}</span>
              <span className="slide-title-chip">{slides[1].title}</span>
            </div>

            <div className="slide-grid split-grid">
              <div>
                <SectionHeading
                  eyebrow="The problem"
                  title="Cardiovascular registries are structurally and semantically heterogeneous"
                  body="The asymmetry between BHS and EHVol is not a formatting nuisance. It is the central blocker that must be addressed before pooled modeling is trustworthy."
                />
                <div className="section-intro-list reveal rise-up">
                  <div className="intro-check">
                    <CheckCircle2 size={18} />
                    <span>Name mismatches: equivalent concepts appear under different labels and prefixes</span>
                  </div>
                  <div className="intro-check">
                    <CheckCircle2 size={18} />
                    <span>Representation mismatches: units, category encodings, and date formats differ by cohort</span>
                  </div>
                  <div className="intro-check">
                    <CheckCircle2 size={18} />
                    <span>Governance constraints: PII handling, provenance, and quality validation are non-negotiable</span>
                  </div>
                </div>
              </div>

              <div className="pillars-row">
                {pillars.map((pillar, index) => (
                  <article key={pillar.title} className="mini-panel reveal rise-up" style={{ animationDelay: `${index * 120}ms` }}>
                    <span className="mini-label">{pillar.label}</span>
                    <h3>{pillar.title}</h3>
                    <p>{pillar.description}</p>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="slide-response" className="slide">
          <div className="slide-shell panel">
            <div className="slide-heading-block">
              <span className="eyebrow">{slides[2].label}</span>
              <span className="slide-title-chip">{slides[2].title}</span>
            </div>

            <SectionHeading
              eyebrow="Method landscape"
              title="A hybrid method stack is the practical response"
              body="The design choice is not manual versus AI. The strongest operating model combines rule-based clinical controls, semantic ML, standards, and governance artifacts."
            />

            <div className="capability-grid capability-grid--deck">
              {capabilities.map((capability, index) => {
                const Icon = capability.icon;

                return (
                  <article key={capability.title} className="capability-card reveal rise-up" style={{ animationDelay: `${index * 70}ms` }}>
                    <span className="card-label">{capability.label}</span>
                    <div className="capability-icon">
                      <Icon size={24} />
                    </div>
                    <h3>{capability.title}</h3>
                    <p>{capability.description}</p>
                    <ul>
                      {capability.bullets.map((bullet) => (
                        <li key={bullet}>{bullet}</li>
                      ))}
                    </ul>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section id="slide-architecture" className="slide">
          <div className="slide-shell panel">
            <div className="slide-heading-block">
              <span className="eyebrow">{slides[3].label}</span>
              <span className="slide-title-chip">{slides[3].title}</span>
            </div>

            <SectionHeading
              eyebrow="Harmonization ecosystem"
              title="From raw registries to interoperable research data"
              body="This is the operating architecture stakeholders are being asked to endorse: layered ingestion, controlled matching, standards-oriented outputs, and explicit interpretation aids."
            />

            <div className="slide-grid architecture-slide-grid">
              <div className="architecture-lanes">
                {architecture.map((lane, index) => {
                  const Icon = lane.icon;

                  return (
                    <article key={lane.title} className="architecture-card reveal rise-up" style={{ animationDelay: `${index * 100}ms` }}>
                      <div className="architecture-title">
                        <Icon size={20} />
                        <h3>{lane.title}</h3>
                      </div>
                      <p>{lane.description}</p>
                      <div className="chip-row">
                        {lane.chips.map((chip) => (
                          <span key={chip} className="chip">{chip}</span>
                        ))}
                      </div>
                    </article>
                  );
                })}
              </div>

              <aside className="architecture-aside reveal rise-up delayed-one">
                <span className="panel-kicker">Interpretation</span>
                <h3>Hybrid harmonization is the practical center</h3>
                <ul className="signal-list">
                  <li>
                    <CheckCircle2 size={18} />
                    Manual rules improve safety and traceability for high-risk clinical fields.
                  </li>
                  <li>
                    <CheckCircle2 size={18} />
                    Semantic embeddings improve concept detection beyond string overlap.
                  </li>
                  <li>
                    <CheckCircle2 size={18} />
                    Distribution checks and quality gates reduce false-positive mappings.
                  </li>
                </ul>
              </aside>
            </div>

            <div className="charts-panel reveal rise-up delayed-one">
              <SystemArchitectureCharts />
            </div>
          </div>
        </section>

        <section id="slide-pipeline" className="slide">
          <div className="slide-shell panel">
            <div className="slide-heading-block">
              <span className="eyebrow">{slides[4].label}</span>
              <span className="slide-title-chip">{slides[4].title}</span>
            </div>

            <SectionHeading
              eyebrow="Data pipeline"
              title="The operating baseline is already implemented"
              body="The project can already be explained as a four-stage flow. That matters because the ask is not speculative research, it is disciplined scale-up."
            />

            <div className="timeline-grid timeline-grid--deck">
              {timeline.map((item, index) => (
                <article key={item.step} className="timeline-card reveal rise-up" style={{ animationDelay: `${index * 120}ms` }}>
                  <span className="timeline-step">{item.step}</span>
                  <h3>{item.title}</h3>
                  <p>{item.description}</p>
                  <ul>
                    {item.outputs.map((output) => (
                      <li key={output}>{output}</li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="slide-benchmark" className="slide">
          <div className="slide-shell panel">
            <div className="slide-heading-block">
              <span className="eyebrow">{slides[5].label}</span>
              <span className="slide-title-chip">{slides[5].title}</span>
            </div>

            <SectionHeading
              eyebrow="Benchmark and standards"
              title="The method choice is aligned with external practice"
              body="Both literature and production ecosystems point toward hybrid semantic pipelines, with OMOP-oriented interoperability and explicit governance rather than opaque automation."
            />

            <div className="slide-grid split-grid benchmark-grid">
              <div className="operations-grid operations-grid--deck">
                {benchmarkCards.map((item, index) => {
                  const Icon = item.icon;

                  return (
                    <article key={item.title} className="operations-card reveal rise-up" style={{ animationDelay: `${index * 90}ms` }}>
                      <span className="card-label">Method</span>
                      <Icon size={22} />
                      <h3>{item.title}</h3>
                      <p>{item.description}</p>
                    </article>
                  );
                })}
              </div>

              <div className="deployment-grid deployment-grid--deck">
                {networkCards.map((item, index) => {
                  const Icon = item.icon;

                  return (
                    <article key={item.title} className="deployment-card reveal rise-up" style={{ animationDelay: `${index * 110}ms` }}>
                      <span className="card-label">Reference</span>
                      <div className="deployment-icon">
                        <Icon size={20} />
                      </div>
                      <h3>{item.title}</h3>
                      <p>{item.description}</p>
                    </article>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        <section id="slide-evidence" className="slide">
          <div className="slide-shell panel visual-section">
            <div className="slide-heading-block">
              <span className="eyebrow">{slides[6].label}</span>
              <span className="slide-title-chip">{slides[6].title}</span>
            </div>

            <SectionHeading
              eyebrow="Operational visibility"
              title="Current interfaces make the story inspectable"
              body="These captures are not aspirational mockups. They are evidence that the narrative is grounded in the current stakeholder presentation and implementation surfaces."
            />

            <div className="screenshot-grid screenshot-grid--deck">
              {productScreens.map((screen, index) => (
                <article
                  key={screen.title}
                  className={`screenshot-card reveal rise-up ${screen.frame === "portrait" ? "screenshot-card--portrait" : ""}`}
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="window-chrome">
                    <span />
                    <span />
                    <span />
                  </div>
                  <div className="screenshot-head">
                    <h3>{screen.title}</h3>
                    <a className="screenshot-open" href={screen.src} target="_blank" rel="noreferrer">
                      Open full capture
                      <ArrowRight size={14} />
                    </a>
                  </div>
                  <div className="screenshot-tags">
                    {screen.tags.map((tag) => (
                      <span key={tag} className="chip">{tag}</span>
                    ))}
                  </div>
                  <div className="screenshot-frame">
                    <img src={screen.src} alt={screen.alt} loading="lazy" decoding="async" />
                  </div>
                  <div className="screenshot-copy">
                    <p>{screen.description}</p>
                    <ul className="screenshot-highlights">
                      {screen.highlights.map((point) => (
                        <li key={point}>{point}</li>
                      ))}
                    </ul>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="slide-governance" className="slide">
          <div className="slide-shell panel governance-shell">
            <div className="slide-heading-block">
              <span className="eyebrow">{slides[7].label}</span>
              <span className="slide-title-chip">{slides[7].title}</span>
            </div>

            <SectionHeading
              eyebrow="Governance criteria"
              title="Translate architecture into measurable program controls"
              body="This slide links technical design to the operating metrics and risk posture that stakeholders can actually govern."
            />

            <div className="slide-grid split-grid">
              <div className="impact-panel-inner">
                <div className="impact-list reveal rise-up">
                  {outcomes.map((outcome) => (
                    <div key={outcome} className="impact-item">
                      <CheckCircle2 size={18} />
                      <span>{outcome}</span>
                    </div>
                  ))}
                </div>

                <div className="impact-aside reveal rise-up delayed-one">
                  <div className="impact-stat">
                    <span>Current cohort scale</span>
                    <strong>4,943 harmonized rows across two cohorts</strong>
                  </div>
                  <div className="impact-stat">
                    <span>Research ambition</span>
                    <strong>Progress toward 10k+ patient-years as cohorts are onboarded</strong>
                  </div>
                  <div className="impact-stat">
                    <span>Core risk if delayed</span>
                    <strong>Inconsistent mappings and slower cohort expansion</strong>
                  </div>
                </div>
              </div>

              <div className="operations-grid operations-grid--deck">
                {operations.map((item, index) => {
                  const Icon = item.icon;

                  return (
                    <article key={item.title} className="operations-card reveal rise-up" style={{ animationDelay: `${index * 90}ms` }}>
                      <span className="card-label">Control</span>
                      <Icon size={22} />
                      <h3>{item.title}</h3>
                      <p>{item.description}</p>
                    </article>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        <section id="slide-decision" className="slide">
          <div className="slide-shell panel decision-shell">
            <div className="slide-heading-block">
              <span className="eyebrow">{slides[8].label}</span>
              <span className="slide-title-chip">{slides[8].title}</span>
            </div>

            <SectionHeading
              eyebrow="Decision"
              title="Select the harmonization architecture now to unlock reliable multi-cohort cardiovascular research"
              body="The implementation proof is in place. The remaining requirement is governance approval to institutionalize the hybrid pattern and fund safe cohort onboarding."
            />

            <div className="deployment-grid deployment-grid--deck" id="contact-flow">
              {deploymentModes.map((item, index) => {
                const Icon = item.icon;

                return (
                  <article key={item.title} className="deployment-card reveal rise-up" style={{ animationDelay: `${index * 110}ms` }}>
                    <span className="card-label">Delivery</span>
                    <div className="deployment-icon">
                      <Icon size={20} />
                    </div>
                    <h3>{item.title}</h3>
                    <p>{item.description}</p>
                  </article>
                );
              })}
            </div>

            <section className="closing-banner reveal rise-up">
              <div>
                <span className="eyebrow">Presentation summary</span>
                <h2>Approve the hybrid semantic architecture, quality gates, and onboarding path.</h2>
                <p>
                  The next strategic step is institutionalizing the current baseline so additional cohorts can be added with
                  faster turnaround, stronger terminology coverage, and explicit governance artifacts.
                </p>
              </div>
              <a className="solid-link" href="/">
                Open BioLink workspace
                <ArrowRight size={16} />
              </a>
            </section>
          </div>
        </section>
      </main>
    </div>
  );
}