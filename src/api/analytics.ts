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

// Get registry overview statistics
export async function getRegistryOverview() {
  return get<RegistryOverview>('/api/analytics/overview');
}

// Get demographics breakdown
export async function getDemographics() {
  return get<DemographicsData>('/api/analytics/demographics');
}

// Get clinical metrics distribution
export async function getClinicalMetrics() {
  return get<ClinicalMetrics>('/api/analytics/clinical');
}

// Get comorbidity analysis
export async function getComorbidities() {
  return get<ComorbidityData>('/api/analytics/comorbidities');
}

// Get lifestyle/smoking statistics
export async function getLifestyleStats() {
  return get<LifestyleStats>('/api/analytics/lifestyle');
}

// Get geographic distribution
export async function getGeographicStats() {
  return get<GeographicStats>('/api/analytics/geographic');
}

// Get enrollment trends
export async function getEnrollmentTrends() {
  return get<EnrollmentTrend[]>('/api/analytics/enrollment-trends');
}

// Get data quality/completeness analysis
export async function getDataQuality() {
  return get<DataQuality>('/api/analytics/data-quality');
}

// Get imaging statistics
export async function getImagingStats() {
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
  }>('/api/analytics/imaging');
}

// Get ECG analysis
export async function getEcgAnalysis() {
  return get<{
    conclusions: Array<{ ecg_conclusion: string; count: number }>;
    abnormalities: {
      p_wave: number;
      qrs: number;
      st_segment: number;
      t_wave: number;
    };
    rhythmDistribution: Array<{ rhythm: string; count: number }>;
  }>('/api/analytics/ecg');
}
