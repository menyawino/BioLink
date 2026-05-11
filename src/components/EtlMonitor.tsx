import { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Progress } from './ui/progress';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Database,
  FileCheck2,
  FileJson2,
  FlaskConical,
  GitBranch,
  Layers3,
  Loader2,
  PlayCircle,
  RefreshCw,
  Send,
  ShieldAlert,
  TableProperties,
  TimerReset,
  TriangleAlert,
  Waypoints,
} from 'lucide-react';
import { getEtlJobStatus, listEtlJobs, runEtl, webhookTrigger, type EtlJobStatus, type EtlRunRequest, type EtlStageManifest } from '../api/etl';

type LineageStageKey = 'ingest' | 'profile' | 'unify' | 'quality' | 'publish';
type LineageStageStatus = 'idle' | 'running' | 'complete' | 'failed' | 'optional';

type LineageBlueprint = {
  key: LineageStageKey;
  title: string;
  subtitle: string;
  description: string;
  inputs: string[];
  outputs: string[];
  owner: string;
  icon: typeof Database;
};

type LineageStage = LineageBlueprint & {
  status: LineageStageStatus;
  metric: string;
};

const LINEAGE_BLUEPRINTS: LineageBlueprint[] = [
  {
    key: 'ingest',
    title: 'Ingest',
    subtitle: 'Acquire source files',
    description: 'Collect BHS and EHVol payloads from mounted CSVs or webhook uploads and stage them for orchestration in NiFi.',
    inputs: ['db/BHS_Full.csv', 'db/EHVol_Full.csv', 'Webhook CSV payload'],
    outputs: ['Canonical staged CSV', 'Trigger token', 'Dataset manifest'],
    owner: 'FastAPI + NiFi trigger',
    icon: Database,
  },
  {
    key: 'profile',
    title: 'Profile & Clean',
    subtitle: 'Prepare cohort data',
    description: 'Run the db/test profiling, range-cleaning, unit extraction, and fuzzy standardization steps before unification.',
    inputs: ['BHS_step_2_reduced.csv', 'EHVol_step_2_reduced.csv', 'Step dictionaries'],
    outputs: ['step_3 to step_6 artifacts', 'Validated cohort slices'],
    owner: 'db/test step pipeline',
    icon: GitBranch,
  },
  {
    key: 'unify',
    title: 'Unify Registry',
    subtitle: 'Merge cohort records',
    description: 'Build the wide unified snapshot from the cleaned db/test outputs and reload the registry tables.',
    inputs: ['step_4 cleaned cohorts', 'step_6 fuzzy suggestions'],
    outputs: ['unified_registry.csv', 'step_7 outputs', 'registry_etl_runs'],
    owner: 'BiolinkRegistryPipelineProcessor',
    icon: Layers3,
  },
  {
    key: 'quality',
    title: 'Quality & Comparability',
    subtitle: 'Assess readiness',
    description: 'Publish the current audit report, cohort characterization, and comparability summary before publication.',
    inputs: ['step_7 unified outputs', 'Comparability rules'],
    outputs: ['data_quality_report.html', 'cohort_characterization.csv', 'comparability_report.json'],
    owner: 'db/test/run_pipeline.py',
    icon: FlaskConical,
  },
  {
    key: 'publish',
    title: 'Publish',
    subtitle: 'Refresh consumers',
    description: 'Optionally refresh Superset-facing datasets and expose the latest run state to external consumers.',
    inputs: ['Validated registry outputs', 'Publication toggle'],
    outputs: ['Superset datasets', 'Programmatic dashboards'],
    owner: 'Superset bridge',
    icon: Send,
  },
];

const POLLABLE_STATUSES = new Set(['queued', 'running']);
const RUNNING_STAGE_INDEX = 2;
const FAILED_STAGE_INDEX = 2;

function asRecord(value: unknown): Record<string, unknown> | null {
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

function formatTimestamp(value: string | null | undefined) {
  if (!value) return 'Not started';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function formatDuration(startedAt: string | null, finishedAt: string | null) {
  if (!startedAt) return 'Waiting';
  const start = new Date(startedAt).getTime();
  const end = finishedAt ? new Date(finishedAt).getTime() : Date.now();
  if (Number.isNaN(start) || Number.isNaN(end)) return 'Unknown';
  const totalSeconds = Math.max(0, Math.round((end - start) / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes === 0) return `${seconds}s`;
  return `${minutes}m ${seconds}s`;
}

function getRequestedDatasets(job: EtlJobStatus | null) {
  const datasets = job?.request?.datasets;
  if (Array.isArray(datasets) && datasets.length > 0) {
    return datasets;
  }
  return ['ehvol', 'bhs'];
}

function statusTone(status: LineageStageStatus) {
  if (status === 'failed') return 'border-red-300 bg-red-50 text-red-900';
  if (status === 'running') return 'border-amber-300 bg-amber-50 text-amber-900';
  if (status === 'complete') return 'border-emerald-300 bg-emerald-50 text-emerald-900';
  if (status === 'optional') return 'border-slate-300 bg-slate-100 text-slate-700';
  return 'border-slate-200 bg-white text-slate-700';
}

function stageStatusLabel(status: LineageStageStatus) {
  if (status === 'running') return 'In flight';
  if (status === 'complete') return 'Complete';
  if (status === 'failed') return 'Blocked';
  if (status === 'optional') return 'Skipped';
  return 'Waiting';
}

function stageSurfaceTone(status: LineageStageStatus, selected: boolean) {
  if (selected) {
    return 'border-slate-900 bg-[linear-gradient(160deg,_rgba(15,23,42,1),_rgba(30,41,59,0.96))] text-white shadow-[0_22px_48px_rgba(15,23,42,0.22)]';
  }
  if (status === 'failed') {
    return 'border-rose-200 bg-[linear-gradient(180deg,_rgba(255,241,242,1),_rgba(255,255,255,0.98))] text-rose-950';
  }
  if (status === 'running') {
    return 'border-amber-200 bg-[linear-gradient(180deg,_rgba(255,251,235,1),_rgba(255,255,255,0.98))] text-amber-950';
  }
  if (status === 'complete') {
    return 'border-emerald-200 bg-[linear-gradient(180deg,_rgba(236,253,245,1),_rgba(255,255,255,0.98))] text-emerald-950';
  }
  if (status === 'optional') {
    return 'border-slate-200 bg-[linear-gradient(180deg,_rgba(248,250,252,1),_rgba(255,255,255,0.98))] text-slate-700';
  }
  return 'border-slate-200 bg-white text-slate-800';
}

function connectorTone(status: LineageStageStatus) {
  if (status === 'failed') return 'bg-rose-300';
  if (status === 'running') return 'bg-amber-300';
  if (status === 'complete') return 'bg-emerald-300';
  if (status === 'optional') return 'bg-slate-300';
  return 'bg-slate-200';
}

function stageDotTone(status: LineageStageStatus, selected: boolean) {
  if (selected) return 'bg-white ring-4 ring-white/15';
  if (status === 'failed') return 'bg-rose-500 ring-4 ring-rose-100';
  if (status === 'running') return 'bg-amber-500 ring-4 ring-amber-100';
  if (status === 'complete') return 'bg-emerald-500 ring-4 ring-emerald-100';
  if (status === 'optional') return 'bg-slate-400 ring-4 ring-slate-100';
  return 'bg-slate-300 ring-4 ring-slate-100';
}

function stageBadgeVariant(status: LineageStageStatus): 'default' | 'secondary' | 'outline' | 'destructive' {
  if (status === 'failed') return 'destructive';
  if (status === 'complete') return 'default';
  if (status === 'running') return 'secondary';
  return 'outline';
}

function getStageManifest(job: EtlJobStatus | null, key: LineageStageKey): EtlStageManifest | null {
  return job?.lineage?.find((stage) => stage.key === key) ?? null;
}

function inferLineageStages(job: EtlJobStatus | null): LineageStage[] {
  const manifestStages = job?.lineage ?? [];
  if (manifestStages.length > 0) {
    return LINEAGE_BLUEPRINTS.map((stage) => {
      const manifest = manifestStages.find((item) => item.key === stage.key);
      if (!manifest) {
        return {
          ...stage,
          status: stage.key === 'publish' && job?.request?.skip_superset ? 'optional' : 'idle',
          metric: stage.description,
        };
      }

      return {
        ...stage,
        status: manifest.status,
        metric: manifest.message || stage.description,
      };
    });
  }

  const requestedDatasets = getRequestedDatasets(job);
  const result = asRecord(job?.result);
  const runMode = typeof result?.mode === 'string' ? result.mode : 'script-aligned';
  const publishSkipped = Boolean(job?.request?.skip_superset);
  const completedStages = job?.status === 'succeeded' ? LINEAGE_BLUEPRINTS.length : job?.status === 'running' ? RUNNING_STAGE_INDEX : job?.status === 'failed' ? FAILED_STAGE_INDEX : job?.status === 'queued' ? 0 : -1;
  const activeStageIndex = job?.status === 'running' ? RUNNING_STAGE_INDEX : job?.status === 'failed' ? FAILED_STAGE_INDEX : job?.status === 'queued' ? 0 : -1;

  return LINEAGE_BLUEPRINTS.map((stage, index) => {
    let status: LineageStageStatus = 'idle';
    if (job?.status === 'succeeded') {
      status = stage.key === 'publish' && publishSkipped ? 'optional' : 'complete';
    } else if (job?.status === 'failed') {
      status = index < activeStageIndex ? 'complete' : index === activeStageIndex ? 'failed' : 'idle';
    } else if (job?.status === 'running') {
      status = index < activeStageIndex ? 'complete' : index === activeStageIndex ? 'running' : 'idle';
    } else if (job?.status === 'queued') {
      status = index === 0 ? 'running' : 'idle';
    }

    if (stage.key === 'publish' && publishSkipped && status === 'idle') {
      status = 'optional';
    }

    let metric = '';
    if (stage.key === 'ingest') {
      metric = `${requestedDatasets.length} dataset${requestedDatasets.length === 1 ? '' : 's'} staged`;
    } else if (stage.key === 'profile') {
      metric = runMode === 'script-aligned' ? 'db/test preparation active' : 'Preparation pending';
    } else if (stage.key === 'unify') {
      metric = job ? `Run window ${formatDuration(job.startedAt, job.finishedAt)}` : 'Awaiting run';
    } else if (stage.key === 'quality') {
      metric = 'Audit artifacts refreshed';
    } else {
      metric = publishSkipped ? 'Superset refresh skipped' : 'Superset refresh enabled';
    }

    return { ...stage, status, metric };
  });
}

function stageProgressPercent(job: EtlJobStatus | null) {
  if (job?.lineage && job.lineage.length > 0) {
    const weightedStages = job.lineage.reduce((total, stage) => {
      if (stage.status === 'complete' || stage.status === 'optional') return total + 1;
      if (stage.status === 'running') return total + 0.5;
      return total;
    }, 0);
    return Math.round((weightedStages / LINEAGE_BLUEPRINTS.length) * 100);
  }
  if (!job) return 0;
  if (job.status === 'queued') return 12;
  if (job.status === 'running') return 58;
  if (job.status === 'failed') return 66;
  return job.request?.skip_superset ? 92 : 100;
}

function statusVariant(status: EtlJobStatus['status']): 'default' | 'secondary' | 'outline' | 'destructive' {
  if (status === 'failed') return 'destructive';
  if (status === 'succeeded') return 'default';
  if (status === 'running') return 'secondary';
  return 'outline';
}

export function EtlMonitor() {
  const datasets: Array<'ehvol' | 'bhs'> = ['ehvol', 'bhs'];
  const [schema, setSchema] = useState('public');
  const [dbtSelect, setDbtSelect] = useState('');
  const [skipSuperset, setSkipSuperset] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [jobs, setJobs] = useState<EtlJobStatus[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [selectedStage, setSelectedStage] = useState<LineageStageKey>('unify');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [csvText, setCsvText] = useState<string | null>(null);
  const [nifiFrameStatus, setNifiFrameStatus] = useState<'loading' | 'loaded' | 'error'>('loading');
  const configuredNifiUrl = (import.meta.env.VITE_NIFI_URL as string | undefined)?.trim();
  const nifiUrl = configuredNifiUrl && configuredNifiUrl.length > 0 ? configuredNifiUrl : '/nifi/';

  const activeJob = useMemo(
    () => jobs.find((job) => job.jobId === activeJobId) ?? null,
    [jobs, activeJobId]
  );

  const selectedJob = activeJob ?? jobs[0] ?? null;
  const hasSelectedJob = Boolean(selectedJob);
  const lineageStages = useMemo(() => inferLineageStages(selectedJob), [selectedJob]);
  const selectedStageDetails = useMemo(
    () => lineageStages.find((stage) => stage.key === selectedStage) ?? lineageStages[0] ?? null,
    [lineageStages, selectedStage]
  );
  const selectedStageManifest = useMemo(
    () => getStageManifest(selectedJob, selectedStage),
    [selectedJob, selectedStage]
  );
  const completedStageCount = useMemo(
    () => lineageStages.filter((stage) => stage.status === 'complete').length,
    [lineageStages]
  );

  const pipelineStats = useMemo(() => {
    const queued = jobs.filter((job) => job.status === 'queued').length;
    const running = jobs.filter((job) => job.status === 'running').length;
    const succeeded = jobs.filter((job) => job.status === 'succeeded').length;
    const failed = jobs.filter((job) => job.status === 'failed').length;
    const successRate = jobs.length > 0 ? Math.round((succeeded / jobs.length) * 100) : 0;
    return { queued, running, succeeded, failed, successRate };
  }, [jobs]);

  const assetRows = useMemo(() => {
    const publishSkipped = Boolean(selectedJob?.request?.skip_superset);
    return [
      {
        name: 'Raw registry sources',
        location: 'db/BHS_Full.csv + db/EHVol_Full.csv',
        stage: 'Ingest',
        freshness: selectedJob ? formatTimestamp(selectedJob.requestedAt) : 'Standing source',
      },
      {
        name: 'Prepared cohort artifacts',
        location: 'db/test/step_3 ... db/test/step_7',
        stage: 'Profile & Clean',
        freshness: selectedJob?.status === 'queued' ? 'Queued for refresh' : 'Regenerated during run',
      },
      {
        name: 'Unified registry',
        location: 'outputs/unified_registry.csv',
        stage: 'Unify Registry',
        freshness: selectedJob ? formatDuration(selectedJob.startedAt, selectedJob.finishedAt) : 'Last successful run',
      },
      {
        name: 'QA artifacts',
        location: 'outputs/data_quality_report.html',
        stage: 'Quality & Comparability',
        freshness: 'Updated after validation stages',
      },
      {
        name: 'Superset datasets',
        location: 'api/superset/programmatic',
        stage: 'Publish',
        freshness: publishSkipped ? 'Skipped on this run' : 'Published when ETL succeeds',
      },
    ];
  }, [selectedJob]);

  const fetchJobs = async () => {
    setIsRefreshing(true);
    const response = await listEtlJobs(20);
    if (response.success && response.data) {
      setJobs(response.data);
      if (!activeJobId && response.data[0]) {
        setActiveJobId(response.data[0].jobId);
      }
      setError(null);
    } else {
      setError(response.error || 'Failed to fetch ETL jobs');
    }
    setIsRefreshing(false);
  };

  const fetchActiveJob = async (jobIdOverride?: string) => {
    const targetJobId = jobIdOverride ?? activeJobId;
    if (!targetJobId) return;
    const response = await getEtlJobStatus(targetJobId);
    if (!(response.success && response.data)) return;

    setJobs((prev) => {
      const rest = prev.filter((job) => job.jobId !== response.data!.jobId);
      return [response.data!, ...rest].sort((a, b) => b.requestedAt.localeCompare(a.requestedAt));
    });
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  useEffect(() => {
    if (!activeJob || !POLLABLE_STATUSES.has(activeJob.status)) return;

    const timer = setInterval(() => {
      fetchActiveJob();
      fetchJobs();
    }, 2000);

    return () => clearInterval(timer);
  }, [activeJob?.status, activeJobId]);

  useEffect(() => {
    if (!selectedJob) return;
    if (selectedJob.status === 'queued') {
      setSelectedStage('ingest');
    } else if (selectedJob.status === 'running' || selectedJob.status === 'failed') {
      setSelectedStage('unify');
    } else {
      setSelectedStage(selectedJob.request?.skip_superset ? 'quality' : 'publish');
    }
  }, [selectedJob?.jobId, selectedJob?.status, selectedJob?.request?.skip_superset]);

  const submitRun = async () => {
    setIsSubmitting(true);
    setError(null);
    setMessage(null);

    const response = await runEtl({
      schema,
      datasets,
      dbt_select: dbtSelect || null,
      skip_superset: skipSuperset,
    });

    if (response.success && response.data) {
      setActiveJobId(response.data.jobId);
      setMessage(response.data.message);
      await fetchJobs();
      await fetchActiveJob(response.data.jobId);
    } else {
      setError(response.error || 'Failed to trigger ETL run');
    }

    setIsSubmitting(false);
  };

  const submitWebhookRun = async () => {
    setIsSubmitting(true);
    setError(null);
    setMessage(null);

    const requestPayload: EtlRunRequest = {
      schema,
      datasets,
      dbt_select: dbtSelect || null,
      skip_superset: skipSuperset,
    };

    if (csvText) {
      requestPayload.csv = csvText;
    }

    const response = await webhookTrigger({ runId: null, request: requestPayload });

    if (response.success && response.data) {
      setActiveJobId(response.data.jobId);
      setMessage(response.data.message || 'ETL job enqueued via webhook');
      await fetchJobs();
      await fetchActiveJob(response.data.jobId);
    } else {
      setError(response.error || 'Failed to trigger webhook ETL run');
    }

    setIsSubmitting(false);
  };

  return (
    <Tabs defaultValue="etl-monitor" className="space-y-4">
      <TabsList className="view-tabs-list w-full justify-start">
        <TabsTrigger value="etl-monitor">ETL Monitor</TabsTrigger>
        <TabsTrigger value="etl-designer">ETL Designer</TabsTrigger>
      </TabsList>

      <TabsContent value="etl-monitor" className="space-y-6">
        <Card className="overflow-hidden border-0 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.18),_transparent_30%),linear-gradient(135deg,_rgba(255,255,255,0.96),_rgba(248,250,252,0.96))] shadow-[0_28px_80px_rgba(15,23,42,0.08)]">
          <CardContent className="p-0">
            <div className={hasSelectedJob ? 'grid gap-0 lg:grid-cols-[1.05fr_0.95fr]' : 'grid gap-0'}>
              <div className="space-y-6 px-6 py-6 md:px-8 md:py-8">
                <div className="space-y-3">
                  <Badge variant="outline" className="border-sky-200 bg-sky-50 text-sky-900">NiFi ETL control room</Badge>
                  <div className="space-y-2">
                    <h2 className="text-2xl font-semibold tracking-tight text-slate-950">Registry pipeline operations without guessing where the flow broke.</h2>
                    <p className="max-w-2xl text-sm leading-6 text-slate-600">
                      Trigger runs, inspect stage progression, and trace every downstream asset from source CSVs to Superset publication inside one monitor.
                    </p>
                  </div>
                </div>

                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                  <div className="rounded-2xl border border-white/80 bg-white/80 p-4 shadow-sm">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Running now</p>
                      <Activity className="h-4 w-4 text-sky-600" />
                    </div>
                    <p className="mt-3 text-3xl font-semibold text-slate-950">{pipelineStats.running}</p>
                    <p className="mt-1 text-sm text-slate-600">Active pipeline jobs</p>
                  </div>
                  <div className="rounded-2xl border border-white/80 bg-white/80 p-4 shadow-sm">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Queued</p>
                      <TimerReset className="h-4 w-4 text-amber-600" />
                    </div>
                    <p className="mt-3 text-3xl font-semibold text-slate-950">{pipelineStats.queued}</p>
                    <p className="mt-1 text-sm text-slate-600">Waiting for worker time</p>
                  </div>
                  <div className="rounded-2xl border border-white/80 bg-white/80 p-4 shadow-sm">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Success rate</p>
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    </div>
                    <p className="mt-3 text-3xl font-semibold text-slate-950">{pipelineStats.successRate}%</p>
                    <p className="mt-1 text-sm text-slate-600">Across the visible run history</p>
                  </div>
                  <div className="rounded-2xl border border-white/80 bg-white/80 p-4 shadow-sm">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Failures</p>
                      <ShieldAlert className="h-4 w-4 text-rose-600" />
                    </div>
                    <p className="mt-3 text-3xl font-semibold text-slate-950">{pipelineStats.failed}</p>
                    <p className="mt-1 text-sm text-slate-600">Runs needing intervention</p>
                  </div>
                </div>

                <div className="grid gap-3 lg:grid-cols-[1.2fr_0.8fr_0.8fr]">
                  <div className="rounded-[1.4rem] border border-slate-200 bg-[linear-gradient(135deg,_rgba(14,116,144,0.08),_rgba(255,255,255,0.94))] p-4 shadow-sm">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Pipeline posture</p>
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      <Badge variant="outline" className="border-sky-200 bg-sky-50 text-sky-900">Script-aligned NiFi flow</Badge>
                      <Badge variant="outline" className="border-slate-300 bg-white text-slate-700">{getRequestedDatasets(selectedJob).join(' + ')}</Badge>
                      <Badge variant="outline" className="border-slate-300 bg-white text-slate-700">{selectedJob?.request?.skip_superset ? 'Publish skipped' : 'Publish enabled'}</Badge>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-slate-600">
                      The monitor reflects the seeded two-stage NiFi topology: schema generation first, then the scripted registry pipeline with OMOP, QA, and publication handoff.
                    </p>
                  </div>
                  <div className="rounded-[1.4rem] border border-slate-200 bg-white p-4 shadow-sm">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Current focus</p>
                    <p className="mt-3 text-lg font-semibold text-slate-950">{selectedStageDetails?.title || 'Harmonize Registry'}</p>
                    <p className="mt-1 text-sm text-slate-600">{selectedStageDetails ? stageStatusLabel(selectedStageDetails.status) : 'Waiting for run selection'}</p>
                  </div>
                  <div className="rounded-[1.4rem] border border-slate-200 bg-white p-4 shadow-sm">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Stage completion</p>
                    <p className="mt-3 text-lg font-semibold text-slate-950">{completedStageCount}/{lineageStages.length}</p>
                    <p className="mt-1 text-sm text-slate-600">Checkpoints cleared for the selected run.</p>
                  </div>
                </div>

                <div className="rounded-[1.5rem] border border-slate-200 bg-white/80 p-5 shadow-sm backdrop-blur">
                  <div className="grid gap-5 xl:grid-cols-2">
                    <div>
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div>
                          <p className="text-sm font-semibold text-slate-950">Trigger a new ETL run</p>
                          <p className="mt-1 max-w-xl text-sm text-slate-600">Use the scripted NiFi path, optionally scope dbt models, and decide whether downstream publication should run.</p>
                        </div>
                        <Badge variant="outline" className="border-slate-300 bg-slate-50 text-slate-700">Datasets fixed: ehvol, bhs</Badge>
                      </div>

                      <div className="mt-5 grid gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <Label htmlFor="etl-schema">Schema</Label>
                          <Input id="etl-schema" value={schema} onChange={(e) => setSchema(e.target.value)} />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="etl-dbt-select">dbt Select</Label>
                          <Input id="etl-dbt-select" value={dbtSelect} onChange={(e) => setDbtSelect(e.target.value)} placeholder="tag:daily or model_name" />
                        </div>
                      </div>

                      <div className="mt-4 flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-3">
                        <div>
                          <p className="text-sm font-medium text-slate-900">Skip Superset refresh</p>
                          <p className="text-xs text-slate-600">Use this when you want lineage and registry outputs refreshed without republishing dashboards.</p>
                        </div>
                        <Switch checked={skipSuperset} onCheckedChange={setSkipSuperset} />
                      </div>

                      <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                        <Button onClick={submitRun} disabled={isSubmitting} className="rounded-full px-5">
                          {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <PlayCircle className="mr-2 h-4 w-4" />}
                          Run scripted ETL
                        </Button>
                        <Button variant="outline" onClick={submitWebhookRun} disabled={isSubmitting} className="rounded-full px-5">
                          {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
                          Run with uploaded CSV
                        </Button>
                        <Button variant="outline" onClick={fetchJobs} disabled={isRefreshing} className="rounded-full px-5 md:col-span-2 xl:col-span-1">
                          {isRefreshing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
                          Refresh jobs
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-4 rounded-[1.3rem] border border-slate-200 bg-slate-50/85 p-4 xl:self-start">
                      <div>
                        <p className="text-sm font-semibold text-slate-950">Ingest payload</p>
                        <p className="mt-1 text-sm text-slate-600">Upload a CSV or paste sample rows for webhook-driven runs.</p>
                      </div>

                      <div className="space-y-2">
                        <Label>Upload CSV payload</Label>
                        <input
                          type="file"
                          accept="text/csv"
                          className="block w-full rounded-2xl border border-dashed border-slate-300 bg-white px-4 py-3 text-sm text-slate-700 file:mr-4 file:rounded-full file:border-0 file:bg-slate-900 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white"
                          onChange={async (event) => {
                            const file = event.target.files?.[0];
                            if (!file) return;
                            const text = await file.text();
                            setCsvText(text);
                          }}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="etl-csv-text">Or paste CSV content</Label>
                        <textarea
                          id="etl-csv-text"
                          className="min-h-40 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 shadow-sm outline-none transition focus:border-slate-400"
                          rows={7}
                          value={csvText ?? ''}
                          onChange={(event) => setCsvText(event.target.value)}
                          placeholder="participant_id,gender,age\n1001,F,63"
                        />
                      </div>

                      {message ? (
                        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">{message}</div>
                      ) : null}
                      {error ? (
                        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">{error}</div>
                      ) : null}

                      {!hasSelectedJob ? (
                        <div className="rounded-2xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <div>
                              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Awaiting first run</p>
                              <p className="mt-1 text-sm text-slate-700">Queue telemetry and result payload panels will activate after the first successful enqueue.</p>
                            </div>
                            <Badge variant="outline" className="border-slate-300 bg-slate-50 text-slate-700">Monitor idle</Badge>
                          </div>
                        </div>
                      ) : null}
                    </div>
                  </div>
                </div>
              </div>

              {hasSelectedJob ? (
              <div className="border-t border-slate-200/80 bg-slate-950 px-6 py-6 text-slate-50 lg:border-l lg:border-t-0 md:px-8 md:py-8">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-400">Active run</p>
                    <h3 className="mt-2 text-xl font-semibold text-white">{selectedJob ? selectedJob.jobId : 'No run selected'}</h3>
                  </div>
                  {selectedJob ? <Badge variant={statusVariant(selectedJob.status)}>{selectedJob.status}</Badge> : null}
                </div>

                <div className="mt-6 space-y-4 rounded-[1.5rem] border border-white/10 bg-white/5 p-5">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm font-medium text-white">Pipeline completion</p>
                      <p className="text-xs text-slate-400">Stage estimate derived from current job state</p>
                    </div>
                    <span className="text-sm font-semibold text-white">{stageProgressPercent(selectedJob)}%</span>
                  </div>
                  <Progress value={stageProgressPercent(selectedJob)} className="h-2.5 bg-white/10 [&_[data-slot=progress-indicator]]:bg-sky-400" />

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Requested</p>
                      <p className="mt-2 text-sm text-white">{selectedJob ? formatTimestamp(selectedJob.requestedAt) : 'No runs yet'}</p>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-black/10 p-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Elapsed</p>
                      <p className="mt-2 text-sm text-white">{selectedJob ? formatDuration(selectedJob.startedAt, selectedJob.finishedAt) : 'Waiting'}</p>
                    </div>
                  </div>

                  <Separator className="bg-white/10" />

                  <div className="space-y-3">
                    <div className="flex items-center justify-between gap-4 text-sm text-slate-300">
                      <span>Datasets</span>
                      <span className="font-medium text-white">{getRequestedDatasets(selectedJob).join(', ')}</span>
                    </div>
                    <div className="flex items-center justify-between gap-4 text-sm text-slate-300">
                      <span>Schema</span>
                      <span className="font-medium text-white">{selectedJob?.request?.schema || schema}</span>
                    </div>
                    <div className="flex items-center justify-between gap-4 text-sm text-slate-300">
                      <span>dbt Select</span>
                      <span className="font-medium text-white">{selectedJob?.request?.dbt_select || 'None'}</span>
                    </div>
                    <div className="flex items-center justify-between gap-4 text-sm text-slate-300">
                      <span>Publication</span>
                      <span className="font-medium text-white">{selectedJob?.request?.skip_superset ? 'Skipped' : 'Superset refresh enabled'}</span>
                    </div>
                  </div>

                  {selectedJob?.error ? (
                    <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                      <div className="flex items-start gap-2">
                        <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />
                        <span>{selectedJob.error}</span>
                      </div>
                    </div>
                  ) : null}

                  <div className="rounded-2xl border border-white/10 bg-black/10 px-4 py-4">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Pipeline heartbeat</p>
                      <span className="text-xs text-slate-400">{completedStageCount} stages complete</span>
                    </div>
                    <div className="mt-4 flex flex-wrap items-center gap-2">
                      {lineageStages.map((stage) => (
                        <div
                          key={stage.key}
                          className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs ${stage.key === selectedStage ? 'border-sky-300/40 bg-sky-400/10 text-white' : 'border-white/10 bg-white/5 text-slate-300'}`}
                        >
                          <span className={`h-2.5 w-2.5 rounded-full ${stage.status === 'running' ? 'animate-pulse' : ''} ${stage.key === selectedStage ? 'bg-sky-300' : stage.status === 'failed' ? 'bg-rose-400' : stage.status === 'running' ? 'bg-amber-400' : stage.status === 'complete' ? 'bg-emerald-400' : stage.status === 'optional' ? 'bg-slate-400' : 'bg-slate-500'}`} />
                          <span>{stage.title}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="mt-6 rounded-[1.5rem] border border-white/10 bg-white/5 p-5">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm font-medium text-white">Recent activity queue</p>
                      <p className="text-xs text-slate-400">Select a run to inspect lineage and outputs.</p>
                    </div>
                    <Badge variant="outline" className="border-white/15 bg-white/5 text-slate-200">{jobs.length} visible</Badge>
                  </div>

                  <ScrollArea className="mt-4 h-[19rem] pr-3">
                    <div className="space-y-3">
                      {jobs.length === 0 ? (
                        <div className="rounded-2xl border border-dashed border-white/10 px-4 py-6 text-sm text-slate-400">No ETL jobs recorded yet.</div>
                      ) : (
                        jobs.map((job) => (
                          <button
                            key={job.jobId}
                            type="button"
                            onClick={() => setActiveJobId(job.jobId)}
                            className={`w-full rounded-2xl border px-4 py-4 text-left transition ${job.jobId === selectedJob?.jobId ? 'border-sky-400 bg-sky-400/10 shadow-[0_18px_36px_rgba(14,165,233,0.18)]' : 'border-white/10 bg-black/10 hover:border-white/20 hover:bg-white/8'}`}
                          >
                            <div className="flex flex-wrap items-center justify-between gap-3">
                              <div className="flex items-center gap-2">
                                <Badge variant={statusVariant(job.status)}>{job.status}</Badge>
                                <span className="text-sm font-medium text-white">{job.jobId}</span>
                              </div>
                              <span className="text-xs text-slate-400">{formatTimestamp(job.requestedAt)}</span>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-300">
                              <span className="rounded-full border border-white/10 px-2.5 py-1">schema={job.request?.schema || 'public'}</span>
                              <span className="rounded-full border border-white/10 px-2.5 py-1">datasets={getRequestedDatasets(job).join(', ')}</span>
                              <span className="rounded-full border border-white/10 px-2.5 py-1">elapsed {formatDuration(job.startedAt, job.finishedAt)}</span>
                            </div>
                          </button>
                        ))
                      )}
                    </div>
                  </ScrollArea>
                </div>
              </div>
              ) : null}
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <CardTitle className="text-xl text-slate-950">Visual lineage manager</CardTitle>
                <CardDescription className="mt-1 max-w-3xl text-sm leading-6">
                  Track how source cohorts move through matching, harmonization, OMOP shaping, quality checks, and publication. The rail below is interactive, connected, and tuned for the scripted NiFi flow rather than a generic status grid.
                </CardDescription>
              </div>
              <Badge variant="outline" className="border-slate-300 bg-slate-50 text-slate-700">Selected run: {selectedJob?.jobId || 'none'}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="rounded-[1.6rem] border border-slate-200 bg-[linear-gradient(180deg,_rgba(248,250,252,0.98),_rgba(255,255,255,1))] p-4 shadow-sm md:p-5">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-slate-950">Scripted pipeline rail</p>
                  <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">Each node maps to a real stage in the NiFi-driven ETL path. Select a node to inspect its inputs, outputs, and operator guidance.</p>
                </div>
                <div className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm">
                  {selectedStageDetails ? `${selectedStageDetails.title}: ${stageStatusLabel(selectedStageDetails.status)}` : 'Select a stage'}
                </div>
              </div>

              <div className="mt-5 overflow-x-auto pb-2">
                <div className="flex min-w-max items-stretch gap-0 pr-4">
                  {lineageStages.map((stage, index) => {
                    const Icon = stage.icon;
                    const isSelected = stage.key === selectedStage;

                    return (
                      <div key={stage.key} className="flex items-center">
                        <button
                          type="button"
                          onClick={() => setSelectedStage(stage.key)}
                          className={`w-[220px] rounded-[1.4rem] border p-4 text-left transition ${stageSurfaceTone(stage.status, isSelected)}`}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className={`text-[11px] font-semibold uppercase tracking-[0.18em] ${isSelected ? 'text-slate-300' : 'text-slate-500'}`}>Stage {index + 1}</p>
                              <p className="mt-2 text-base font-semibold">{stage.title}</p>
                            </div>
                            <span className={`inline-flex h-11 w-11 items-center justify-center rounded-2xl ${isSelected ? 'bg-white/10 text-white' : 'bg-slate-900 text-white'}`}>
                              <Icon className="h-4 w-4" />
                            </span>
                          </div>

                          <div className="mt-5 flex items-center gap-3">
                            <span className={`h-3 w-3 rounded-full ${stage.status === 'running' ? 'animate-pulse' : ''} ${stageDotTone(stage.status, isSelected)}`} />
                            <span className={`text-sm font-medium ${isSelected ? 'text-white' : 'text-slate-700'}`}>{stageStatusLabel(stage.status)}</span>
                          </div>

                          <p className={`mt-4 text-sm leading-6 ${isSelected ? 'text-slate-200' : 'text-slate-600'}`}>{stage.metric}</p>
                          <p className={`mt-2 text-xs ${isSelected ? 'text-slate-400' : 'text-slate-500'}`}>{stage.subtitle}</p>
                        </button>

                        {index < lineageStages.length - 1 ? (
                          <div className="flex w-14 shrink-0 items-center justify-center px-2">
                            <div className={`h-1 w-full rounded-full ${connectorTone(stage.status)}`} />
                          </div>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
              <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm">
                {selectedStageDetails ? (
                  <>
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{selectedStageDetails.subtitle}</p>
                        <h3 className="mt-2 text-xl font-semibold text-slate-950">{selectedStageDetails.title}</h3>
                        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">{selectedStageDetails.description}</p>
                      </div>
                      <Badge variant={stageBadgeVariant(selectedStageDetails.status)}>{selectedStageDetails.status}</Badge>
                    </div>

                    <div className="mt-5 grid gap-3 md:grid-cols-3">
                      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Stage state</p>
                        <p className="mt-2 text-base font-semibold text-slate-950">{stageStatusLabel(selectedStageDetails.status)}</p>
                      </div>
                      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Operator metric</p>
                        <p className="mt-2 text-base font-semibold text-slate-950">{selectedStageDetails.metric}</p>
                      </div>
                      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Owner</p>
                        <p className="mt-2 text-base font-semibold text-slate-950">{selectedStageDetails.owner}</p>
                      </div>
                    </div>

                    <div className="mt-6 grid gap-4 md:grid-cols-2">
                      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        <p className="text-sm font-semibold text-slate-900">Inputs</p>
                        <ul className="mt-3 space-y-2 text-sm text-slate-600">
                          {selectedStageDetails.inputs.map((input) => (
                            <li key={input} className="flex items-start gap-2">
                              <ArrowRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-400" />
                              <span>{input}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        <p className="text-sm font-semibold text-slate-900">Outputs</p>
                        <ul className="mt-3 space-y-2 text-sm text-slate-600">
                          {selectedStageDetails.outputs.map((output) => (
                            <li key={output} className="flex items-start gap-2">
                              <FileCheck2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-400" />
                              <span>{output}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    <div className="mt-4 grid gap-4 md:grid-cols-3">
                      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                        <span className="font-semibold text-slate-900">Stage owner:</span> {selectedStageDetails.owner}
                      </div>
                      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                        <span className="font-semibold text-slate-900">Observed via:</span> {selectedStageManifest?.source || 'Derived monitor state'}
                      </div>
                      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                        <span className="font-semibold text-slate-900">Observed at:</span> {selectedStageManifest ? formatTimestamp(selectedStageManifest.observedAt) : 'Not observed'}
                      </div>
                    </div>
                  </>
                ) : null}
              </div>

              <div className="rounded-[1.5rem] border border-slate-200 bg-[linear-gradient(180deg,_rgba(248,250,252,0.96),_rgba(255,255,255,0.98))] p-5 shadow-sm">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-slate-950">Selected run output</p>
                    <p className="mt-1 text-sm text-slate-600">Snapshot of the result payload and run metadata surfaced by the current backend contract.</p>
                  </div>
                  <Waypoints className="h-5 w-5 text-slate-400" />
                </div>

                {selectedJob?.result ? (
                  <pre className="mt-4 max-h-[24rem] overflow-auto rounded-2xl border border-slate-200 bg-slate-950 p-4 text-xs leading-6 text-slate-100">{JSON.stringify(selectedJob.result, null, 2)}</pre>
                ) : (
                  <div className="mt-4 rounded-2xl border border-dashed border-slate-300 px-4 py-6 text-sm text-slate-600">
                    <p className="font-medium text-slate-900">No structured result payload yet.</p>
                    <p className="mt-2 leading-6">Once a run executes, this panel will show the backend response for the selected job so you can compare orchestration status with lineage stage state.</p>
                  </div>
                )}
              </div>
            </div>

            <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
              <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-slate-950">Asset ledger</p>
                    <p className="mt-1 text-sm text-slate-600">Every major artifact tied to the lineage rail above.</p>
                  </div>
                  <FileJson2 className="h-5 w-5 text-slate-400" />
                </div>
                <div className="mt-4 space-y-3">
                  {assetRows.map((asset) => (
                    <div key={asset.name} className="rounded-2xl border border-slate-200 bg-slate-50/80 px-4 py-4">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <p className="text-sm font-semibold text-slate-900">{asset.name}</p>
                        <Badge variant="outline" className="border-slate-300 bg-white text-slate-700">{asset.stage}</Badge>
                      </div>
                      <p className="mt-2 text-sm text-slate-600">{asset.location}</p>
                      <p className="mt-1 text-xs text-slate-500">{asset.freshness}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-slate-950">Operational cues</p>
                    <p className="mt-1 text-sm text-slate-600">Quick guidance based on the current job selection and pipeline state.</p>
                  </div>
                  <Activity className="h-5 w-5 text-slate-400" />
                </div>
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Most likely next operator action</p>
                    <p className="mt-2 text-sm leading-6 text-slate-700">
                      {selectedJob?.status === 'failed'
                        ? 'Inspect the harmonization stage and NiFi processor errors before re-running.'
                        : selectedJob?.status === 'running'
                          ? 'Monitor registry load completion, then confirm OMOP and QA outputs are refreshed.'
                          : selectedJob?.status === 'queued'
                            ? 'Wait for NiFi worker pickup or check for backlog in the processor group.'
                            : 'Review the latest artifacts and decide whether publication should remain enabled.'}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Run contract</p>
                    <p className="mt-2 text-sm leading-6 text-slate-700">
                      Existing API endpoints stay unchanged. This monitor derives stage state from job status, request flags, and result payloads rather than introducing a new backend dependency.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="etl-designer">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle>NiFi Interface</CardTitle>
            <CardDescription>
              Stay in the embedded canvas for low-level processor control. Use the monitor tab when you need operational context, lineage, and artifact awareness.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm text-muted-foreground">
                View and control pipelines directly in Apache NiFi.
              </p>
              <Button variant="outline" onClick={() => window.open(nifiUrl, '_blank', 'noopener,noreferrer')}>
                Open NiFi in new tab
              </Button>
            </div>

            <div className="w-full h-[70vh] border rounded-md overflow-hidden bg-background">
              <iframe
                key={nifiUrl}
                title="Apache NiFi"
                src={nifiUrl}
                className="w-full h-full"
                referrerPolicy="no-referrer"
                onLoad={() => setNifiFrameStatus('loaded')}
                onError={() => setNifiFrameStatus('error')}
              />
            </div>

            {nifiFrameStatus === 'loading' ? (
              <p className="text-xs text-muted-foreground">
                Loading NiFi from {nifiUrl}...
              </p>
            ) : null}

            {nifiFrameStatus === 'loaded' ? (
              <p className="text-xs text-muted-foreground">
                Embedded NiFi URL: {nifiUrl}
              </p>
            ) : null}

            {nifiFrameStatus === 'error' ? (
              <p className="text-xs text-destructive">
                Embedded NiFi failed to load. Use “Open NiFi in new tab” and verify the URL/certificate.
              </p>
            ) : null}

            <p className="text-xs text-muted-foreground">
              NiFi URL source: {configuredNifiUrl && configuredNifiUrl.length > 0 ? 'VITE_NIFI_URL' : 'default /nifi/ proxy path'}.
            </p>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}
