import { useQuery, useMutation } from './useApi';
import { queryCohort, getCohortSummary, exportCohort, downloadCohortCsv } from '../api/cohort';
import type { CohortCriteria, CohortQueryResult, CohortSummary, Patient } from '../api/types';
import { getPatients, type PatientsQueryParams } from '../api/patients';

// Hook for cohort query
export function useCohortQuery() {
  return useMutation<Patient[], PatientsQueryParams>(
    (params) => getPatients(params).then(res => res || [])
  );
}

// Hook for cohort summary
export function useCohortSummary() {
  return useMutation<CohortSummary, number[]>(getCohortSummary);
}

// Hook for cohort export
export function useCohortExport() {
  return useMutation<Patient[], { patientIds: number[]; fields?: string[] }>(
    ({ patientIds, fields }) => exportCohort(patientIds, fields)
  );
}

// Hook for cohort estimate
export function useCohortEstimate(params: PatientsQueryParams) {
  return useQuery<{ count: number }>(
    async () => {
      const patients = await getPatients({ ...params, limit: 1000 });
      return { count: patients?.length || 0 };
    },
    [JSON.stringify(params)], // Track all params changes
    { enabled: true }
  );
}

// Hook for downloading cohort as CSV
export function useDownloadCohort() {
  return useMutation<void, Patient[]>(
    (patients) => {
      downloadCohortCsv(patients, 'cohort_export.csv');
      return Promise.resolve();
    }
  );
}
