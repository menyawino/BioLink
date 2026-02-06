import { useQuery, useMutation } from './useApi';
import {
  getPatients,
  getPatient,
  searchPatients,
  getPatientVitals,
  getPatientImaging,
  getPatientRiskFactors,
  getPatientGenomics,
  type PatientsQueryParams,
} from '../api/patients';
import type { Patient, PatientDetail, PatientVitals, ImagingData, RiskFactors, GenomicData } from '../api/types';

// Hook for fetching paginated patients
export function usePatients(params: PatientsQueryParams = {}) {
  return useQuery<Patient[]>(
    () => getPatients(params),
    [params.page, params.limit, params.search, params.gender, params.ageMin, params.ageMax, params.sortBy, params.sortOrder]
  );
}

// Hook for fetching a single patient
export function usePatient(dnaId: string) {
  return useQuery<PatientDetail>(
    () => getPatient(dnaId),
    [dnaId],
    { enabled: !!dnaId }
  );
}

// Hook for searching patients
export function usePatientSearch(query: string, limit = 20) {
  return useQuery<Patient[]>(
    () => searchPatients(query, limit),
    [query, limit],
    { enabled: query.length > 0 }
  );
}

// Hook for patient vitals
export function usePatientVitals(dnaId: string) {
  return useQuery<PatientVitals>(
    () => getPatientVitals(dnaId),
    [dnaId],
    { enabled: !!dnaId }
  );
}

// Hook for patient imaging data
export function usePatientImaging(dnaId: string) {
  return useQuery<ImagingData>(
    () => getPatientImaging(dnaId),
    [dnaId],
    { enabled: !!dnaId }
  );
}

// Hook for patient risk factors
export function usePatientRiskFactors(dnaId: string) {
  return useQuery<RiskFactors>(
    () => getPatientRiskFactors(dnaId),
    [dnaId],
    { enabled: !!dnaId }
  );
}

// Hook for patient genomics data
export function usePatientGenomics(dnaId: string) {
  return useQuery<GenomicData>(
    () => getPatientGenomics(dnaId),
    [dnaId],
    { enabled: !!dnaId }
  );
}
