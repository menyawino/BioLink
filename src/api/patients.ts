import { get, post } from './client';
import type {
  Patient,
  PatientDetail,
  PatientVitals,
  RiskFactors,
  ImagingData,
  GenomicData,
} from './types';

export interface PatientsQueryParams {
  page?: number;
  limit?: number;
  search?: string;
  gender?: string;
  ageMin?: number;
  ageMax?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  
  // Data availability filters
  hasEcho?: boolean;
  hasMri?: boolean;
  hasGenomics?: boolean;
  hasLabs?: boolean;
  hasImaging?: boolean;
  minDataCompleteness?: number;
  
  // Geographic filters
  nationality?: string;
  region?: string;
  
  // Temporal filters
  enrollmentDateFrom?: string;
  enrollmentDateTo?: string;
  
  // Clinical/risk factor filters
  hasDiabetes?: boolean;
  hasHypertension?: boolean;
  hasSmoking?: boolean;
  hasObesity?: boolean;
  hasFamilyHistory?: boolean;
}

// Get paginated list of patients
export async function getPatients(params: PatientsQueryParams = {}) {
  const queryParams = new URLSearchParams();
  
  if (params.page) queryParams.set('page', params.page.toString());
  if (params.limit) queryParams.set('limit', params.limit.toString());
  if (params.search) queryParams.set('search', params.search);
  if (params.gender) queryParams.set('gender', params.gender);
  if (params.ageMin) queryParams.set('ageMin', params.ageMin.toString());
  if (params.ageMax) queryParams.set('ageMax', params.ageMax.toString());
  if (params.sortBy) queryParams.set('sortBy', params.sortBy);
  if (params.sortOrder) queryParams.set('sortOrder', params.sortOrder);
  
  // Data availability filters
  if (params.hasEcho !== undefined) queryParams.set('hasEcho', params.hasEcho.toString());
  if (params.hasMri !== undefined) queryParams.set('hasMri', params.hasMri.toString());
  if (params.hasGenomics !== undefined) queryParams.set('hasGenomics', params.hasGenomics.toString());
  if (params.hasLabs !== undefined) queryParams.set('hasLabs', params.hasLabs.toString());
  if (params.hasImaging !== undefined) queryParams.set('hasImaging', params.hasImaging.toString());
  if (params.minDataCompleteness) queryParams.set('minDataCompleteness', params.minDataCompleteness.toString());
  
  // Geographic filters
  if (params.nationality) queryParams.set('nationality', params.nationality);
  if (params.region) queryParams.set('region', params.region);
  
  // Temporal filters
  if (params.enrollmentDateFrom) queryParams.set('enrollmentDateFrom', params.enrollmentDateFrom);
  if (params.enrollmentDateTo) queryParams.set('enrollmentDateTo', params.enrollmentDateTo);
  
  // Clinical/risk factor filters
  if (params.hasDiabetes !== undefined) queryParams.set('hasDiabetes', params.hasDiabetes.toString());
  if (params.hasHypertension !== undefined) queryParams.set('hasHypertension', params.hasHypertension.toString());
  if (params.hasSmoking !== undefined) queryParams.set('hasSmoking', params.hasSmoking.toString());
  if (params.hasObesity !== undefined) queryParams.set('hasObesity', params.hasObesity.toString());
  if (params.hasFamilyHistory !== undefined) queryParams.set('hasFamilyHistory', params.hasFamilyHistory.toString());
  
  const query = queryParams.toString();
  return get<Patient[]>(`/api/patients${query ? `?${query}` : ''}`);
}

// Get single patient by DNA ID
export async function getPatient(dnaId: string) {
  return get<PatientDetail>(`/api/patients/${dnaId}`);
}

// Search patients
export async function searchPatients(query: string, limit = 20) {
  return get<Patient[]>(`/api/patients/search/${encodeURIComponent(query)}?limit=${limit}`);
}

// Get patient vitals
export async function getPatientVitals(dnaId: string) {
  return get<PatientVitals>(`/api/patients/${dnaId}/vitals`);
}

// Get patient imaging data
export async function getPatientImaging(dnaId: string) {
  return get<ImagingData>(`/api/patients/${dnaId}/imaging`);
}

// Get patient risk factors
export async function getPatientRiskFactors(dnaId: string) {
  return get<RiskFactors>(`/api/patients/${dnaId}/risk-factors`);
}

// Get patient genomics data
export async function getPatientGenomics(dnaId: string) {
  return get<GenomicData>(`/api/patients/${dnaId}/genomics`);
}
