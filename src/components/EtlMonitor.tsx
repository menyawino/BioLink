import { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Badge } from './ui/badge';
import { Loader2, RefreshCw } from 'lucide-react';
import { getEtlJobStatus, listEtlJobs, runEtl, webhookTrigger, type EtlJobStatus, type EtlRunRequest } from '../api/etl';

const POLLABLE_STATUSES = new Set(['queued', 'running']);

function statusVariant(status: EtlJobStatus['status']): 'default' | 'secondary' | 'outline' | 'destructive' {
  if (status === 'failed') return 'destructive';
  if (status === 'succeeded') return 'default';
  if (status === 'running') return 'secondary';
  return 'outline';
}

export function EtlMonitor() {
  const [table, setTable] = useState('ehvol_full');
  const [schema, setSchema] = useState('public');
  const [dbtSelect, setDbtSelect] = useState('');
  const [skipSuperset, setSkipSuperset] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [jobs, setJobs] = useState<EtlJobStatus[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [csvText, setCsvText] = useState<string | null>(null);
  const [nifiFrameStatus, setNifiFrameStatus] = useState<'loading' | 'loaded' | 'error'>('loading');
  const [nifiUrlIndex, setNifiUrlIndex] = useState(0);

  const nifiUrls = useMemo(() => {
    const configured = import.meta.env.VITE_NIFI_URL as string | undefined;
    if (configured && configured.trim().length > 0) {
      return [configured.trim()];
    }
    if (typeof window === 'undefined') {
      return ['https://localhost:8443/nifi', 'http://localhost:8443/nifi'];
    }
    const host = window.location.hostname || 'localhost';
    return [`https://${host}:8443/nifi`, `http://${host}:8443/nifi`];
  }, []);

  const nifiUrl = nifiUrls[Math.min(nifiUrlIndex, nifiUrls.length - 1)];

  useEffect(() => {
    setNifiFrameStatus('loading');
  }, [nifiUrl]);

  const activeJob = useMemo(
    () => jobs.find((job) => job.jobId === activeJobId) ?? null,
    [jobs, activeJobId]
  );

  const fetchJobs = async () => {
    setIsRefreshing(true);
    const response = await listEtlJobs(20);
    if (response.success && response.data) {
      setJobs(response.data);
      setError(null);
    } else {
      setError(response.error || 'Failed to fetch ETL jobs');
    }
    setIsRefreshing(false);
  };

  const fetchActiveJob = async () => {
    if (!activeJobId) return;
    const response = await getEtlJobStatus(activeJobId);
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

  const submitRun = async () => {
    setIsSubmitting(true);
    setError(null);
    setMessage(null);

    const response = await runEtl({
      table,
      schema,
      dbt_select: dbtSelect || null,
      skip_superset: skipSuperset,
    });

    if (response.success && response.data) {
      setActiveJobId(response.data.jobId);
      setMessage(response.data.message);
      await fetchJobs();
      await fetchActiveJob();
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
      table,
      schema,
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
      await fetchActiveJob();
    } else {
      setError(response.error || 'Failed to trigger webhook ETL run');
    }

    setIsSubmitting(false);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>ETL Run Control</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="etl-table">Table</Label>
              <Input id="etl-table" value={table} onChange={(e) => setTable(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="etl-schema">Schema</Label>
              <Input id="etl-schema" value={schema} onChange={(e) => setSchema(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="etl-dbt-select">dbt Select (optional)</Label>
              <Input id="etl-dbt-select" value={dbtSelect} onChange={(e) => setDbtSelect(e.target.value)} placeholder="tag:daily or model_name" />
            </div>
          </div>

          <div className="flex items-center justify-between border rounded-md px-3 py-2">
            <div>
              <p className="text-sm">Skip Superset refresh</p>
              <p className="text-xs text-muted-foreground">Runs ETL without publishing to Superset.</p>
            </div>
            <Switch checked={skipSuperset} onCheckedChange={setSkipSuperset} />
          </div>

          <div className="flex items-center gap-2">
            <Button onClick={submitRun} disabled={isSubmitting}>
              {isSubmitting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
              Run ETL
            </Button>
            <Button onClick={submitWebhookRun} disabled={isSubmitting}>
              {isSubmitting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
              Run ETL (Webhook / Any CSV)
            </Button>
            <Button variant="outline" onClick={fetchJobs} disabled={isRefreshing}>
              {isRefreshing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
              Refresh
            </Button>
          </div>

          <div className="space-y-2">
            <Label>Upload CSV (optional)</Label>
            <input
              type="file"
              accept="text/csv"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                const text = await file.text();
                setCsvText(text);
              }}
            />
            <Label>or paste CSV content</Label>
            <textarea
              className="w-full border rounded p-2"
              rows={6}
              value={csvText ?? ''}
              onChange={(e) => setCsvText(e.target.value)}
            />
          </div>

          {message ? <p className="text-sm text-green-700">{message}</p> : null}
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>NiFi Interface</CardTitle>
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
              onError={() => {
                const hasFallback = nifiUrlIndex < nifiUrls.length - 1;
                if (hasFallback) {
                  setNifiUrlIndex((prev) => prev + 1);
                  return;
                }
                setNifiFrameStatus('error');
              }}
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
            If this panel stays blank, open NiFi in a new tab once and accept the local HTTPS certificate, then refresh this page.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>ETL Job Status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {jobs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No ETL jobs yet.</p>
          ) : (
            jobs.map((job) => (
              <div key={job.jobId} className="border rounded-md p-3 space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Badge variant={statusVariant(job.status)}>{job.status}</Badge>
                    <span className="text-sm font-medium">{job.jobId}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">{new Date(job.requestedAt).toLocaleString()}</span>
                </div>

                <div className="text-xs text-muted-foreground">
                  table={job.request?.table || 'ehvol_full'} schema={job.request?.schema || 'public'}
                </div>

                {job.error ? <p className="text-xs text-destructive">{job.error}</p> : null}

                {job.result ? (
                  <pre className="text-xs bg-muted rounded p-2 overflow-x-auto">{JSON.stringify(job.result, null, 2)}</pre>
                ) : null}
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
