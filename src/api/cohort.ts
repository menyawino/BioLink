import { post } from './client';
import type {
  CohortCriteria,
  CohortQueryResult,
  CohortSummary,
  Patient,
} from './types';

// Execute cohort query
export async function queryCohort(criteria: CohortCriteria) {
  return post<CohortQueryResult>('/api/cohort/query', criteria);
}

// Get cohort summary statistics
export async function getCohortSummary(patientIds: number[]) {
  return post<CohortSummary>('/api/cohort/summary', { patientIds });
}

// Export cohort data
export async function exportCohort(patientIds: number[], fields?: string[]) {
  return post<Patient[]>('/api/cohort/export', { patientIds, fields });
}

// Helper function to download cohort as CSV
export function downloadCohortCsv(data: Record<string, unknown>[], filename = 'cohort_export.csv') {
  if (data.length === 0) return;
  
  const headers = Object.keys(data[0]);
  const csvRows = [
    headers.join(','),
    ...data.map(row =>
      headers.map(header => {
        const value = row[header];
        if (value === null || value === undefined) return '';
        if (typeof value === 'string' && value.includes(',')) {
          return `"${value}"`;
        }
        return String(value);
      }).join(',')
    )
  ];
  
  const csvContent = csvRows.join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
