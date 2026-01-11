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

// Alias for useRegistryOverview - used by RegistryAnalytics
export function useRegistryStats() {
  return useQuery<RegistryOverview>(getRegistryOverview, []);
}

// Hook for registry overview
export function useRegistryOverview() {
  return useQuery<RegistryOverview>(getRegistryOverview, []);
}

// Hook for demographics data
export function useDemographics() {
  return useQuery<DemographicsData>(getDemographics, []);
}

// Hook for data completeness - uses data quality endpoint
export function useDataCompleteness() {
  return useQuery<DataQuality>(getDataQuality, []);
}

// Hook for geographic data
export function useGeographicData() {
  return useQuery<GeographicStats>(getGeographicStats, []);
}

// Hook for clinical metrics
export function useClinicalMetrics() {
  return useQuery<ClinicalMetrics>(getClinicalMetrics, []);
}

// Hook for comorbidities
export function useComorbidities() {
  return useQuery<ComorbidityData>(getComorbidities, []);
}

// Hook for lifestyle statistics
export function useLifestyleStats() {
  return useQuery<LifestyleStats>(getLifestyleStats, []);
}

// Hook for geographic statistics
export function useGeographicStats() {
  return useQuery<GeographicStats>(getGeographicStats, []);
}

// Hook for enrollment trends
export function useEnrollmentTrends() {
  return useQuery<EnrollmentTrend[]>(getEnrollmentTrends, []);
}

// Hook for data quality
export function useDataQuality() {
  return useQuery<DataQuality>(getDataQuality, []);
}

// Hook for imaging statistics
export function useImagingStats() {
  return useQuery<{
    echo: { avg_ef: number; min_ef: number; max_ef: number; std_ef: number; total: number };
    mri: { avg_lv_ef: number; avg_lv_mass: number; avg_lv_edv: number; total: number };
  }>(getImagingStats, []);
}

// Hook for ECG analysis
export function useEcgAnalysis() {
  return useQuery<{
    conclusions: Array<{ ecg_conclusion: string; count: number }>;
    abnormalities: { p_wave: number; qrs: number; st_segment: number; t_wave: number };
    rhythmDistribution: Array<{ rhythm: string; count: number }>;
  }>(getEcgAnalysis, []);
}
