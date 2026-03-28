import { useQuery } from './useApi';
import {
  getHarmonizationDictionary,
  getHarmonizationTiers,
  getProvenanceSummary,
  getComparabilityReport,
} from '../api/harmonization';
import type {
  HarmonizationDictionaryField,
  HarmonizationTier,
  ProvenanceSummary,
  ComparabilityReport,
} from '../api/types';

export function useHarmonizationDictionary() {
  return useQuery<{
    data: HarmonizationDictionaryField[];
    total: number;
  }>(() => getHarmonizationDictionary(), []);
}

export function useHarmonizationTiers() {
  return useQuery<{
    data: HarmonizationTier[];
    summary: Record<string, number>;
  }>(() => getHarmonizationTiers(), []);
}

export function useProvenanceSummary() {
  return useQuery<ProvenanceSummary>(() => getProvenanceSummary(), []);
}

export function useComparabilityReport() {
  return useQuery<ComparabilityReport>(() => getComparabilityReport(), []);
}
