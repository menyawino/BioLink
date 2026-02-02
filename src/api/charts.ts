import { get, post } from './client';
import type { ChartConfig, ChartFields } from './types';

export interface ChartDataRequest {
  xAxis: string;
  yAxis?: string;
  groupBy?: string;
  filters?: Record<string, any>;
  aggregation?: 'count' | 'avg' | 'sum' | 'min' | 'max';
}

export interface ChartFilter {
  field: string;
  operator: '=' | '!=';
  value: string;
}

export interface ChartSeriesRequest {
  xAxis: string;
  yAxis?: string;
  groupBy?: string;
  aggregation?: 'count' | 'avg' | 'sum' | 'min' | 'max';
  bins?: number;
  limit?: number;
  filters?: ChartFilter[];
}

// Get chart data with flexible parameters
export async function getChartData(params: ChartDataRequest) {
  const queryString = new URLSearchParams({
    xAxis: params.xAxis,
    ...(params.yAxis && { yAxis: params.yAxis }),
    ...(params.groupBy && { groupBy: params.groupBy }),
    ...(params.aggregation && { aggregation: params.aggregation })
  });
  return get<any>(`/api/charts/data?${queryString}`);
}

// Get chart series for rich visuals
export async function getChartSeries(params: ChartSeriesRequest) {
  const queryString = new URLSearchParams({
    xAxis: params.xAxis,
    ...(params.yAxis && { yAxis: params.yAxis }),
    ...(params.groupBy && { groupBy: params.groupBy }),
    ...(params.aggregation && { aggregation: params.aggregation }),
    ...(params.bins && { bins: String(params.bins) }),
    ...(params.limit && { limit: String(params.limit) }),
    ...(params.filters && params.filters.length > 0 ? { filters: JSON.stringify(params.filters) } : {})
  });
  return get<{ label: string; value: number; series?: string }[]>(`/api/charts/series?${queryString}`);
}

// Generate chart data based on configuration
export async function generateChartData(config: ChartConfig) {
  return post<unknown[]>('/api/charts/generate', config);
}

// Get available chart fields
export async function getChartFields() {
  return get<ChartFields>('/api/charts/fields');
}

// Get correlation data between two fields
export async function getCorrelationData(field1: string, field2: string) {
  return get<unknown[]>(`/api/charts/correlation?field1=${field1}&field2=${field2}`);
}

// Get age distribution data - uses the demographics endpoint
export async function getAgeDistribution() {
  const response = await get<{ ageGender: { age_group: string; male: number; female: number }[] }>('/api/analytics/demographics');
  // Transform the nested data to a flat array
  if (response.success && response.data?.ageGender) {
    return {
      success: true,
      data: response.data.ageGender.map(item => ({
        age_group: item.age_group,
        count: (Number(item.male) || 0) + (Number(item.female) || 0)
      }))
    };
  }
  return { success: false, data: [] };
}

// Get gender distribution data - uses the overview endpoint
export async function getGenderDistribution() {
  const response = await get<{ maleCount: number; femaleCount: number }>('/api/analytics/overview');
  if (response.success && response.data) {
    return {
      success: true,
      data: [
        { gender: 'Male', count: response.data.maleCount || 0 },
        { gender: 'Female', count: response.data.femaleCount || 0 }
      ]
    };
  }
  return { success: false, data: [] };
}

// Get scatter plot data - uses correlation endpoint
export async function getScatterData(xField: string, yField: string) {
  const response = await get<Array<Record<string, any>>>(`/api/charts/correlation?field1=${xField}&field2=${yField}`);
  if (response.success && Array.isArray(response.data)) {
    // Map field names to the actual column names returned by the API
    const fieldMap: Record<string, string> = {
      'age': 'age',
      'bmi': 'bmi',
      'systolic_bp': 'systolic_bp',
      'diastolic_bp': 'diastolic_bp',
      'heart_rate': 'heart_rate',
      'hba1c': 'hba1c',
      'ef': 'ef',
      'troponin_i': 'troponin_i',
      'lv_ejection_fraction': 'lv_ejection_fraction',
      'lv_mass': 'lv_mass'
    };
    
    const xCol = fieldMap[xField] || xField;
    const yCol = fieldMap[yField] || yField;
    
    return {
      success: true,
      data: response.data
        .filter(item => item[xCol] != null && item[yCol] != null)
        .map(item => ({
          x: Number(item[xCol]) || 0,
          y: Number(item[yCol]) || 0
        }))
        .filter(item => !isNaN(item.x) && !isNaN(item.y))
    };
  }
  return { success: false, data: [] };
}

// Get data completeness - uses overview endpoint
export async function getDataCompleteness() {
  const response = await get<{ dataCompleteness: string; withMri: number; withEcho: number; withEcg: number; totalPatients: number }>('/api/analytics/overview');
  if (response.success && response.data) {
    const total = response.data.totalPatients || 1;
    return {
      success: true,
      data: {
        overall: parseFloat(response.data.dataCompleteness) || 0,
        mri: Math.round((response.data.withMri / total) * 100),
        echo: Math.round((response.data.withEcho / total) * 100),
        ecg: Math.round((response.data.withEcg / total) * 100)
      }
    };
  }
  return { success: false, data: {} };
}
