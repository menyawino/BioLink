/**
 * App Context - Global state management for agent-driven UI
 */

import React, { createContext, useContext, useState, useCallback } from 'react';

export type ViewType = 'welcome' | 'patient' | 'registry' | 'cohort' | 'analytics' | 'charts' | 'dictionary' | 'settings' | 'profile';

interface AppContextType {
  // Navigation state
  currentView: ViewType;
  setCurrentView: (view: ViewType) => void;
  
  // Patient state
  selectedPatient: string | null;
  setSelectedPatient: (dnaId: string | null) => void;
  
  // Cohort state
  cohortResults: any[];
  setCohortResults: (results: any[]) => void;
  cohortCriteria: any;
  setCohortCriteria: (criteria: any) => void;
  
  // Chart state
  chartConfig: any;
  setChartConfig: (config: any) => void;
  
  // Agent actions (for tool executor)
  navigateToView: (view: ViewType) => void;
  openPatientProfile: (dnaId: string) => void;
  buildCohort: (criteria: any) => void;
  createChart: (config: any) => void;
  
  // Loading/busy state
  isProcessing: boolean;
  setIsProcessing: (processing: boolean) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  // Navigation
  const [currentView, setCurrentView] = useState<ViewType>('welcome');
  
  // Patient
  const [selectedPatient, setSelectedPatient] = useState<string | null>(null);
  
  // Cohort
  const [cohortResults, setCohortResults] = useState<any[]>([]);
  const [cohortCriteria, setCohortCriteria] = useState<any>({});
  
  // Chart
  const [chartConfig, setChartConfig] = useState<any>(null);
  
  // Loading
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Agent-driven actions
  const navigateToView = useCallback((view: ViewType) => {
    setCurrentView(view);
  }, []);
  
  const openPatientProfile = useCallback((dnaId: string) => {
    setSelectedPatient(dnaId);
    setCurrentView('patient');
  }, []);
  
  const buildCohort = useCallback((criteria: any) => {
    setCohortCriteria(criteria);
    setCurrentView('cohort');
  }, []);
  
  const createChart = useCallback((config: any) => {
    setChartConfig(config);
    setCurrentView('charts');
  }, []);
  
  return (
    <AppContext.Provider
      value={{
        currentView,
        setCurrentView,
        selectedPatient,
        setSelectedPatient,
        cohortResults,
        setCohortResults,
        cohortCriteria,
        setCohortCriteria,
        chartConfig,
        setChartConfig,
        navigateToView,
        openPatientProfile,
        buildCohort,
        createChart,
        isProcessing,
        setIsProcessing
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}
