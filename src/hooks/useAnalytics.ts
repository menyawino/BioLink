import { useQuery } from './useApi';
import {
  getRegistryOverview,
  getDemographics,
  getClinicalMetrics,
  getComorbidities,
  getLifestyleStats,
  getGeographicStats,
  getEnrollmentTrends,
  getDataQuality,
  getImagingStats,
  getEcgAnalysis,
} from '../api/analytics';
import type {
  RegistryOverview,
  DemographicsData,
  ClinicalMetrics,
  ComorbidityData,
  LifestyleStats,
  GeographicStats,
  EnrollmentTrend,
  DataQuality,
} from '../api/types';
import type { DatasetFilter } from '../api/patients';

// Alias for useRegistryOverview - used by RegistryAnalytics
export function useRegistryStats(dataset: DatasetFilter = 'combined') {
  return useQuery<RegistryOverview>(() => getRegistryOverview(dataset), [dataset]);
}

// Hook for registry overview
export function useRegistryOverview(dataset: DatasetFilter = 'combined') {
  return useQuery<RegistryOverview>(() => getRegistryOverview(dataset), [dataset]);
}

// Hook for demographics data
export function useDemographics(dataset: DatasetFilter = 'combined') {
  return useQuery<DemographicsData>(() => getDemographics(dataset), [dataset]);
}

// Hook for data completeness - uses data quality endpoint
export function useDataCompleteness(dataset: DatasetFilter = 'combined') {
  return useQuery<DataQuality>(() => getDataQuality(dataset), [dataset]);
}

// Hook for geographic data
export function useGeographicData(dataset: DatasetFilter = 'combined') {
  return useQuery<GeographicStats>(() => getGeographicStats(dataset), [dataset]);
}

// Hook for clinical metrics
export function useClinicalMetrics(dataset: DatasetFilter = 'combined') {
  return useQuery<ClinicalMetrics>(() => getClinicalMetrics(dataset), [dataset]);
}

// Hook for comorbidities
export function useComorbidities(dataset: DatasetFilter = 'combined') {
  return useQuery<ComorbidityData>(() => getComorbidities(dataset), [dataset]);
}

// Hook for lifestyle statistics
export function useLifestyleStats(dataset: DatasetFilter = 'combined') {
  return useQuery<LifestyleStats>(() => getLifestyleStats(dataset), [dataset]);
}

// Hook for geographic statistics
export function useGeographicStats(dataset: DatasetFilter = 'combined') {
  return useQuery<GeographicStats>(() => getGeographicStats(dataset), [dataset]);
}

// Hook for enrollment trends
export function useEnrollmentTrends(dataset: DatasetFilter = 'combined') {
  return useQuery<EnrollmentTrend[]>(() => getEnrollmentTrends(dataset), [dataset]);
}

// Hook for data quality
export function useDataQuality(dataset: DatasetFilter = 'combined') {
  return useQuery<DataQuality>(() => getDataQuality(dataset), [dataset]);
}

// Hook for imaging statistics
export function useImagingStats(dataset: DatasetFilter = 'combined') {
  return useQuery<{
    echo: { avg_ef: number; min_ef: number; max_ef: number; std_ef: number; total: number };
    mri: { avg_lv_ef: number; avg_lv_mass: number; avg_lv_edv: number; total: number };
  }>(() => getImagingStats(dataset), [dataset]);
}

// Hook for ECG analysis
export function useEcgAnalysis(dataset: DatasetFilter = 'combined') {
  return useQuery<{
    conclusions: Array<{ ecg_conclusion: string; count: number }>;
    abnormalities: { p_wave: number; qrs: number; st_segment: number; t_wave: number };
    rhythmDistribution: Array<{ rhythm: string; count: number }>;
  }>(() => getEcgAnalysis(dataset), [dataset]);
}
