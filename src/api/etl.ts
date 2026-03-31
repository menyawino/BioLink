import { get, post, type ApiResponse } from './client';

export interface EtlRunRequest {
  table?: string;
  schema?: string;
  csv?: string | null;
  datasets?: Array<'ehvol' | 'bhs'>;
  dataset_name?: string | null;
  dbt_select?: string | null;
  skip_superset?: boolean;
}

export interface EtlRunAccepted {
  jobId: string;
  status: 'queued';
  message: string;
}

export interface EtlStageManifest {
  key: 'ingest' | 'match' | 'harmonize' | 'omop' | 'quality' | 'publish';
  status: 'idle' | 'running' | 'complete' | 'failed' | 'optional';
  source: string;
  message: string;
  observedAt: string;
  details?: Record<string, unknown>;
}

export interface EtlJobStatus {
  jobId: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed';
  requestedAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  request: EtlRunRequest;
  result: unknown;
  error: string | null;
  lineage?: EtlStageManifest[];
}

export async function runEtl(payload: EtlRunRequest): Promise<ApiResponse<EtlRunAccepted>> {
  return post<EtlRunAccepted>('/api/etl/run', payload);
}

export async function webhookTrigger(payload: { runId?: string | null; request?: EtlRunRequest }): Promise<ApiResponse<EtlRunAccepted & { externalRunId?: string | null }>> {
  return post('/api/etl/webhook/trigger', payload);
}

export async function getEtlJobStatus(jobId: string): Promise<ApiResponse<EtlJobStatus>> {
  return get<EtlJobStatus>(`/api/etl/status/${jobId}`);
}

export async function listEtlJobs(limit = 20): Promise<ApiResponse<EtlJobStatus[]>> {
  return get<EtlJobStatus[]>(`/api/etl/status?limit=${limit}`);
}
