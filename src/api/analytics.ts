import { get } from './client';
import type {
  RegistryOverview,
  DemographicsData,
  ClinicalMetrics,
  ComorbidityData,
  LifestyleStats,
  GeographicStats,
  EnrollmentTrend,
  DataQuality,
} from './types';
import type { DatasetFilter } from './patients';

function withDataset(path: string, dataset: DatasetFilter = 'all') {
  const params = new URLSearchParams();
  params.set('dataset', dataset);
  return `${path}?${params.toString()}`;
}

// Get registry overview statistics
export async function getRegistryOverview(dataset: DatasetFilter = 'all') {
  return get<RegistryOverview>(withDataset('/api/analytics/overview', dataset));
}

// Get demographics breakdown
export async function getDemographics(dataset: DatasetFilter = 'all') {
  return get<DemographicsData>(withDataset('/api/analytics/demographics', dataset));
}

// Get clinical metrics distribution
export async function getClinicalMetrics(dataset: DatasetFilter = 'all') {
  return get<ClinicalMetrics>(withDataset('/api/analytics/clinical', dataset));
}

// Get comorbidity analysis
export async function getComorbidities(dataset: DatasetFilter = 'all') {
  return get<ComorbidityData>(withDataset('/api/analytics/comorbidities', dataset));
}

// Get lifestyle/smoking statistics
export async function getLifestyleStats(dataset: DatasetFilter = 'all') {
  return get<LifestyleStats>(withDataset('/api/analytics/lifestyle', dataset));
}

// Get geographic distribution
export async function getGeographicStats(dataset: DatasetFilter = 'all') {
  return get<GeographicStats>(withDataset('/api/analytics/geographic', dataset));
}

// Get governorate-level geographic data
export async function getGovernorateGeographicStats(dataset: DatasetFilter = 'all') {
  return get<MapData[]>(withDataset('/api/analytics/geographic-governorates', dataset));
}

// Get enrollment trends
export async function getEnrollmentTrends(dataset: DatasetFilter = 'all') {
  return get<EnrollmentTrend[]>(withDataset('/api/analytics/enrollment-trends', dataset));
}

// Get data quality/completeness analysis
export async function getDataQuality(dataset: DatasetFilter = 'all') {
  return get<DataQuality>(withDataset('/api/analytics/data-quality', dataset));
}

// Get imaging statistics
export async function getImagingStats(dataset: DatasetFilter = 'all') {
  return get<{
    echo: {
      avg_ef: number;
      min_ef: number;
      max_ef: number;
      std_ef: number;
      total: number;
    };
    mri: {
      avg_lv_ef: number;
      avg_lv_mass: number;
      avg_lv_edv: number;
      total: number;
    };
  }>(withDataset('/api/analytics/imaging', dataset));
}

// Get ECG analysis
export async function getEcgAnalysis(dataset: DatasetFilter = 'all') {
  return get<{
    conclusions: Array<{ ecg_conclusion: string; count: number }>;
    abnormalities: {
      p_wave: number;
      qrs: number;
      st_segment: number;
      t_wave: number;
    };
    rhythmDistribution: Array<{ rhythm: string; count: number }>;
  }>(withDataset('/api/analytics/ecg', dataset));
}
