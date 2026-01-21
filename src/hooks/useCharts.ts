import { useQuery, useMutation } from './useApi';
import { 
  generateChartData, 
  getChartFields, 
  getCorrelationData,
  getAgeDistribution,
  getGenderDistribution,
  getScatterData,
  getDataCompleteness,
  getChartSeries
} from '../api/charts';
import type { ChartConfig, ChartFields } from '../api/types';
import type { ChartSeriesRequest } from '../api/charts';

// Hook for generating chart data
export function useChartData() {
  return useMutation<unknown[], ChartConfig>(generateChartData);
}

// Hook for chart fields
export function useChartFields() {
  return useQuery<ChartFields>(getChartFields, []);
}

// Hook for correlation data
export function useCorrelationData(field1: string, field2: string) {
  return useQuery<unknown[]>(
    () => getCorrelationData(field1, field2),
    [field1, field2],
    { enabled: !!field1 && !!field2 }
  );
}

// Hook for age distribution
export function useAgeDistribution() {
  return useQuery<{ age_group: string; count: number }[]>(
    getAgeDistribution,
    []
  );
}

// Hook for gender distribution
export function useGenderDistribution() {
  return useQuery<{ gender: string; count: number }[]>(
    getGenderDistribution,
    []
  );
}

// Hook for scatter plot data
export function useScatterData(xField: string, yField: string) {
  return useQuery<{ x: number; y: number }[]>(
    () => getScatterData(xField, yField),
    [xField, yField],
    { enabled: !!xField && !!yField }
  );
}

// Hook for chart series data
export function useChartSeries(params: ChartSeriesRequest, enabled: boolean = true) {
  const key = JSON.stringify(params);
  return useQuery<{ label: string; value: number; series?: string }[]>(
    () => getChartSeries(params),
    [key],
    { enabled }
  );
}

// Hook for data completeness
export function useDataCompleteness() {
  return useQuery<Record<string, number>>(
    getDataCompleteness,
    []
  );
}
