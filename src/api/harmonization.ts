import { get } from './client';
import type {
  HarmonizationDictionaryField,
  HarmonizationTier,
  ProvenanceRecord,
  ProvenanceSummary,
  ComparabilityReport,
} from './types';

export async function getHarmonizationDictionary() {
  return get<HarmonizationDictionaryField[]>('/api/harmonization/dictionary');
}

// Get harmonization tier classification for all variables
export async function getHarmonizationTiers() {
  return get<{
    data: HarmonizationTier[];
    summary: Record<string, number>;
  }>('/api/harmonization/tiers');
}

// Get provenance records with optional filters
export async function getProvenanceRecords(params?: {
  master_col?: string;
  validation_status?: string;
  cohort?: string;
  limit?: number;
  offset?: number;
}) {
  const search = new URLSearchParams();
  if (params?.master_col) search.set('master_col', params.master_col);
  if (params?.validation_status) search.set('validation_status', params.validation_status);
  if (params?.cohort) search.set('cohort', params.cohort);
  if (params?.limit) search.set('limit', String(params.limit));
  if (params?.offset) search.set('offset', String(params.offset));
  const qs = search.toString();
  return get<{
    data: ProvenanceRecord[];
    total: number;
  }>(`/api/harmonization/provenance${qs ? `?${qs}` : ''}`);
}

// Get aggregated provenance statistics
export async function getProvenanceSummary() {
  return get<ProvenanceSummary>('/api/harmonization/provenance/summary');
}

// Get cohort comparability analysis report
export async function getComparabilityReport() {
  return get<ComparabilityReport>('/api/harmonization/comparability');
}
