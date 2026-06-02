import { Suspense, lazy, useEffect, useState, useCallback } from "react";
import { AppProvider, useApp } from "./context/AppContext";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Sidebar } from "./components/Sidebar";
import { PatientHeader } from "./components/PatientHeader";
import { PatientSearch } from "./components/PatientSearch";
import { VitalSigns } from "./components/VitalSigns";
import { RiskFactors } from "./components/RiskFactors";
import { MedicalHistory } from "./components/MedicalHistory";
import { TraditionalImaging } from "./components/TraditionalImaging";
import { GenomicData } from "./components/GenomicData";
import { SampleData } from "./components/SampleData";
import { DataNotAvailable } from "./components/DataNotAvailable";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { KeyboardShortcutsHelp } from "./components/KeyboardShortcutsHelp";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Button } from "./components/ui/button";
import { Drawer, DrawerContent, DrawerHeader, DrawerTitle } from "./components/ui/drawer";
import { useIsMobile } from "./components/ui/use-mobile";
import { usePatient, usePatientGenomics } from "./hooks/usePatients";
import { useKeyboardShortcuts, getAppShortcuts } from "./hooks/useKeyboardShortcuts";
import { canAccessView } from "./lib/access";
import type { ViewType } from "./context/AppContext";
import type { GenomicData as GenomicDataResponse, PatientDetail } from "./api/types";
import { cn } from "./components/ui/utils";
import { Menu } from "lucide-react";

const ChatInterface = lazy(() => import("./components/ChatInterface").then((module) => ({ default: module.ChatInterface })));
const PatientRegistryTable = lazy(() => import("./components/PatientRegistryTable").then((module) => ({ default: module.PatientRegistryTable })));
const RegistryAnalytics = lazy(() => import("./components/RegistryAnalytics").then((module) => ({ default: module.RegistryAnalytics })));
const SupersetWorkspace = lazy(() => import("./components/SupersetWorkspace").then((module) => ({ default: module.SupersetWorkspace })));
const EtlMonitor = lazy(() => import("./components/EtlMonitor").then((module) => ({ default: module.EtlMonitor })));
const CohortBuilder = lazy(() => import("./components/CohortBuilder").then((module) => ({ default: module.CohortBuilder })));
const DataDictionary = lazy(() => import("./components/DataDictionary").then((module) => ({ default: module.DataDictionary })));
const Settings = lazy(() => import("./components/Settings").then((module) => ({ default: module.Settings })));
const UserProfile = lazy(() => import("./components/UserProfile").then((module) => ({ default: module.UserProfile })));
const LoginPage = lazy(() => import("./components/LoginPage").then((module) => ({ default: module.LoginPage })));

const VIEW_LABELS: Record<ViewType, string> = {
  welcome: "Welcome",
  patient: "Patient Profile",
  registry: "Patient Registry",
  cohort: "Cohort Builder",
  analytics: "Registry Analytics",
  charts: "Chart Builder",
  etl: "ETL Monitor",
  dictionary: "Data Dictionary",
  settings: "Settings",
  profile: "Profile",
};

// Transform patient data from API to component format
function transformPatientToHeader(patient: PatientDetail) {
  const getRiskLevel = (): 'low' | 'moderate' | 'high' => {
    const hasHypertension = patient.medical?.high_blood_pressure;
    const hasDiabetes = patient.medical?.diabetes_mellitus;
    const hasHeartAttack = patient.medical?.heart_attack_or_angina;
    const hasHeartFailure = patient.medical?.prior_heart_failure;
    const age = Number(patient.age) || 0;
    
    if (hasHeartAttack || hasHeartFailure) return 'high';
    if ((hasHypertension && hasDiabetes) || age > 65) return 'moderate';
    return 'low';
  };

  return {
    id: patient.dna_id,
    mrn: patient.dna_id,
    name: patient.dna_id,
    age: Number(patient.age) || 0,
    gender: patient.gender === 'M' ? 'Male' : patient.gender === 'F' ? 'Female' : patient.gender || 'Unknown',
    dateOfBirth: patient.date_of_birth || 'Not recorded',
    phone: 'Not in database',
    address: patient.current_city || 'Not recorded',
    riskLevel: getRiskLevel(),
    lastVisit: patient.enrollment_date || 'Not recorded'
  };
}

function transformToVitals(patient: PatientDetail) {
  const hasPhysicalData = patient.physical !== null;
  const systolic = hasPhysicalData ? Number(patient.physical?.systolic_bp) || null : null;
  const diastolic = hasPhysicalData ? Number(patient.physical?.diastolic_bp) || null : null;
  const heartRate = hasPhysicalData ? Number(patient.physical?.heart_rate) || null : null;
  const weight = hasPhysicalData ? Number(patient.physical?.weight_kg) || null : null;
  
  return {
    hasData: hasPhysicalData && (systolic !== null || diastolic !== null || heartRate !== null),
    current: {
      systolic: systolic ?? 0,
      diastolic: diastolic ?? 0,
      heartRate: heartRate ?? 0,
      temperature: null as number | null,
      weight: weight ?? 0,
      cholesterol: {
        total: null as number | null,
        ldl: null as number | null,
        hdl: null as number | null
      }
    },
    history: systolic && diastolic && heartRate ? [
      { date: "Enrollment", systolic, diastolic, heartRate }
    ] : []
  };
}

function transformToRiskFactors(patient: PatientDetail) {
  const hasMedicalData = patient.medical !== null;
  const hasLifestyleData = patient.lifestyle !== null;
  const hasPhysicalData = patient.physical !== null;
  
  return {
    hasData: hasMedicalData || hasLifestyleData || hasPhysicalData,
    hypertension: patient.medical?.high_blood_pressure ?? false,
    diabetes: patient.medical?.diabetes_mellitus ?? false,
    smoking: patient.lifestyle?.current_smoker ?? false,
    familyHistory: patient.family?.family_disease_info !== null && patient.family?.family_disease_info !== undefined,
    obesity: hasPhysicalData && patient.physical?.bmi ? (Number(patient.physical.bmi) >= 30) : false,
    sedentary: false,
    age: Number(patient.age) || 0,
    bmi: hasPhysicalData ? Number(patient.physical?.bmi) || 0 : 0
  };
}

function transformToMedicalHistory(patient: PatientDetail) {
  const diagnoses = patient.medical?.diagnoses ?? [];
  const hasLabsData = patient.labs !== null;
  
  const tests: Array<{
    id: string;
    name: string;
    date: string;
    result: string;
    status: "normal" | "abnormal";
    notes?: string;
  }> = [];
  if (hasLabsData && patient.labs) {
    if (patient.labs.hba1c !== null) {
      tests.push({
        id: "T001",
        name: "HbA1c",
        date: patient.enrollment_date || "Not recorded",
        result: `${Number(patient.labs.hba1c).toFixed(1)}%`,
        status: Number(patient.labs.hba1c) > 6.5 ? "abnormal" : "normal",
        notes: patient.labs.hba1c_outlier ? "Flagged as outlier" : undefined
      });
    }
    if (patient.labs.troponin_i !== null) {
      tests.push({
        id: "T002",
        name: "Troponin I",
        date: patient.enrollment_date || "Not recorded",
        result: `${Number(patient.labs.troponin_i).toFixed(2)} ng/L`,
        status: Number(patient.labs.troponin_i) > 14 ? "abnormal" : "normal",
        notes: patient.labs.troponin_outlier ? "Flagged as outlier" : undefined
      });
    }
  }
  
  return {
    hasData: diagnoses.length > 0 || tests.length > 0,
    diagnoses,
    procedures: [],
    tests,
    longitudinalData: []
  };
}

function transformToImagingData(patient: PatientDetail) {
  const hasEcho = patient.echo !== null && !patient.echo?.missing_echo;
  const hasMri = patient.mri !== null && !patient.mri?.missing_mri;
  const hasAssets = true;
  
  const ct: any[] = [];
  const mri: any[] = [];
  const echo: any[] = [];

  if (hasEcho && patient.echo) {
    echo.push({
      id: "ECHO001",
      date: patient.echo.echo_date || patient.enrollment_date || "Not recorded",
      type: "Transthoracic Echocardiogram",
      indication: "EHVol Study Assessment",
      measurements: {
        ef: Number(patient.echo.ef) || 0,
        lv: `LVEDD: ${patient.echo.lvedd ? Number(patient.echo.lvedd).toFixed(1) : 'N/A'}mm, LVESD: ${patient.echo.lvesd ? Number(patient.echo.lvesd).toFixed(1) : 'N/A'}mm`,
        rv: `RV: ${patient.echo.right_ventricle ? Number(patient.echo.right_ventricle).toFixed(1) : 'N/A'}mm`,
        valves: [
          patient.echo.mitral_regurge ? `MR: ${patient.echo.mitral_regurge}` : null,
          patient.echo.aortic_regurge ? `AR: ${patient.echo.aortic_regurge}` : null,
          patient.echo.tricuspid_regurge ? `TR: ${patient.echo.tricuspid_regurge}` : null
        ].filter(Boolean).join(', ') || 'Not recorded'
      },
      findings: `EF: ${patient.echo.ef ? Number(patient.echo.ef).toFixed(0) : 'N/A'}%, FS: ${patient.echo.fs ? Number(patient.echo.fs).toFixed(1) : 'N/A'}%`,
      cardiologist: "EHVol Study",
      images: []
    });
  }

  if (hasMri && patient.mri) {
    mri.push({
      id: "MRI001",
      date: patient.mri.mri_date || patient.enrollment_date || "Not recorded",
      sequence: "Cardiac MRI",
      fieldStrength: "1.5T",
      indication: "EHVol Study Assessment",
      findings: `LVEF: ${patient.mri.lv_ejection_fraction ? Number(patient.mri.lv_ejection_fraction).toFixed(0) : 'N/A'}%, RVEF: ${patient.mri.rv_ejection_fraction ? Number(patient.mri.rv_ejection_fraction).toFixed(0) : 'N/A'}%`,
      measurements: {
        ejectionFraction: Number(patient.mri.lv_ejection_fraction) || 0,
        lvMass: patient.mri.lv_mass ? `${Number(patient.mri.lv_mass).toFixed(1)}g` : 'N/A',
        lvEdv: patient.mri.lv_end_diastolic_volume ? `${Number(patient.mri.lv_end_diastolic_volume).toFixed(1)}mL` : 'N/A',
        lvEsv: patient.mri.lv_end_systolic_volume ? `${Number(patient.mri.lv_end_systolic_volume).toFixed(1)}mL` : 'N/A'
      },
      radiologist: "EHVol Study",
      images: []
    });
  }

  return { 
    hasData: hasEcho || hasMri || hasAssets,
    ct, 
    mri, 
    echo 
  };
}

export default function App() {
  return (
    <AuthProvider>
      <AppProvider>
        <AuthGate />
      </AppProvider>
    </AuthProvider>
  );
}

function AuthGate() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <FullscreenLoader />;
  }

  if (!isAuthenticated) {
    return (
      <Suspense fallback={<FullscreenLoader />}>
        <LoginPage />
      </Suspense>
    );
  }

  return <AppContent />;
}

function AppContent() {
  const { user } = useAuth();
  const { currentView, setCurrentView, selectedPatient, setSelectedPatient } = useApp();
  const isMobile = useIsMobile();
  const [currentTab, setCurrentTab] = useState<string>("vitals");
  const [displayedView, setDisplayedView] = useState<ViewType>(currentView);
  const [displayedPatient, setDisplayedPatient] = useState<string | null>(selectedPatient);
  const [transitionPhase, setTransitionPhase] = useState<"enter" | "exit" | "idle">("enter");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [shortcutsHelpOpen, setShortcutsHelpOpen] = useState(false);
  const { data: patient, error: patientError, isLoading: patientLoading } = usePatient(selectedPatient || '');
  const { data: genomicsData, error: genomicsError, isLoading: genomicsLoading } = usePatientGenomics(selectedPatient || '');

  // Keyboard shortcuts
  const navigateToView = useCallback((view: string) => {
    setCurrentView(view as ViewType);
  }, [setCurrentView]);

  useKeyboardShortcuts(
    getAppShortcuts(navigateToView, {
      toggleSidebar: () => setMobileNavOpen(prev => !prev),
      openSearch: () => {
        setCurrentView('registry');
      },
      openChat: () => setCurrentView('welcome'),
      openSettings: () => setCurrentView('settings'),
      openHelp: () => setShortcutsHelpOpen(true),
      goBack: () => {
        if (currentView === 'patient') {
          setSelectedPatient(null);
          setCurrentView('registry');
        } else if (currentView !== 'welcome') {
          setCurrentView('welcome');
        }
      },
    })
  );

  useEffect(() => {
    if (!canAccessView(user, currentView as never)) {
      setCurrentView("welcome");
    }
  }, [currentView, setCurrentView, user]);

  useEffect(() => {
    const targetKey = `${currentView}:${selectedPatient ?? "none"}`;
    const displayedKey = `${displayedView}:${displayedPatient ?? "none"}`;

    if (targetKey === displayedKey) {
      return;
    }

    setTransitionPhase("exit");
    const timer = window.setTimeout(() => {
      setDisplayedView(currentView);
      setDisplayedPatient(selectedPatient);
      setTransitionPhase("enter");
    }, 150);

    return () => window.clearTimeout(timer);
  }, [currentView, displayedPatient, displayedView, selectedPatient]);

  useEffect(() => {
    if (transitionPhase !== "enter") {
      return;
    }

    const timer = window.setTimeout(() => {
      setTransitionPhase("idle");
    }, 320);

    return () => window.clearTimeout(timer);
  }, [transitionPhase]);
  
  const handlePatientSelect = (dnaId: string) => {
    setSelectedPatient(dnaId);
    setCurrentView("patient");
  };

  const handleViewChange = (view: ViewType) => {
    setCurrentView(view);
    setMobileNavOpen(false);
  };
  
  return (
    <>
      <div className={cn("app-shell bg-background", isMobile ? "min-h-screen" : "flex h-screen overflow-hidden")}>
        {!isMobile ? (
          <Sidebar currentView={currentView} onViewChange={handleViewChange} className="app-sidebar-panel flex-shrink-0" />
        ) : null}

        {isMobile ? (
          <Drawer direction="left" open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
            <DrawerContent className="app-mobile-drawer w-[88vw] max-w-[22rem] border-r-0 bg-transparent p-0">
              <DrawerHeader className="sr-only">
                <DrawerTitle>BioLink navigation</DrawerTitle>
              </DrawerHeader>
              <Sidebar
                currentView={currentView}
                onViewChange={handleViewChange}
                className="app-sidebar-panel app-mobile-sidebar h-full w-full border-r-0"
              />
            </DrawerContent>
          </Drawer>
        ) : null}

        <div className="app-main flex-1 overflow-auto">
          {isMobile ? (
            <div className="app-mobile-topbar sticky top-0 z-20 mb-3 flex items-center justify-between gap-3 border-b border-border/70 bg-background/88 px-4 py-3 backdrop-blur-xl md:hidden">
              <div className="min-w-0">
                <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-primary/80">BioLink</p>
                <p className="truncate text-base font-semibold text-foreground">{VIEW_LABELS[currentView] ?? "BioLink"}</p>
              </div>
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="shrink-0"
                aria-label="Open navigation menu"
                onClick={() => setMobileNavOpen(true)}
              >
                <Menu className="h-4 w-4" />
              </Button>
            </div>
          ) : null}
          <div
            key={`${displayedView}:${displayedPatient ?? 'none'}`}
            className={`app-stage app-stage-${transitionPhase}`}
            data-view={displayedView}
          >
            <ErrorBoundary componentName={VIEW_LABELS[displayedView]}>
              <Suspense fallback={<ViewLoadingState view={displayedView} />}>
                {renderContent(
                  user,
                  displayedView,
                  displayedPatient,
                  setSelectedPatient,
                  currentTab,
                  setCurrentTab,
                  patient,
                  patientError,
                  patientLoading,
                  genomicsData,
                  genomicsError,
                  genomicsLoading,
                  handlePatientSelect
                )}
              </Suspense>
            </ErrorBoundary>
          </div>
        </div>
      </div>
      <KeyboardShortcutsHelp open={shortcutsHelpOpen} onOpenChange={setShortcutsHelpOpen} />
    </>
  );
}

function renderContent(
  user: import("./types/auth").AuthUser | null,
  currentView: string,
  selectedPatient: string | null,
  setSelectedPatient: (id: string | null) => void,
  currentTab: string,
  setCurrentTab: (tab: string) => void,
  patient: any,
  patientError: any,
  patientLoading: boolean,
  genomicsData: GenomicDataResponse | undefined,
  genomicsError: string | null,
  genomicsLoading: boolean,
  handlePatientSelect: (dnaId: string) => void
) {
  const renderMainContent = () => {
    if (!canAccessView(user, currentView as never)) {
      return <ChatInterface />;
    }

    switch (currentView) {
      case "welcome":
        return <ChatInterface />;
      case "registry":
        return <PatientRegistryTable onPatientSelect={handlePatientSelect} />;
      case "patient":
        if (!selectedPatient) {
          return <PatientSearch currentMrn="" onPatientSelect={setSelectedPatient} />;
        }
        return renderPatientView(
          selectedPatient,
          currentTab,
          setCurrentTab,
          patient,
          patientError,
          patientLoading,
          genomicsData,
          genomicsError,
          genomicsLoading
        );
      case "analytics":
        return <RegistryAnalytics />;
      case "cohort":
        return <CohortBuilder />;
      case "charts":
        return <SupersetWorkspace />;
      case "etl":
        return <EtlMonitor />;
      case "dictionary":
        return <DataDictionary />;
      case "settings":
        return <Settings />;
      case "profile":
        return <UserProfile />;
      default:
        return <ChatInterface />;
    }
  };
  
  return renderMainContent();
}

function FullscreenLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
    </div>
  );
}

function ViewLoadingState({ view }: { view: ViewType }) {
  return (
    <div className="view-loading-shell">
      <div className="view-loading-header space-y-2">
        <span className="section-kicker">Loading View</span>
        <h2 className="section-title capitalize">{view}</h2>
        <p className="section-subtitle">Preparing the next workspace and loading its data dependencies.</p>
      </div>
      <div className="view-loading-grid">
        <div className="view-loading-card view-loading-card-lg" />
        <div className="view-loading-card" />
        <div className="view-loading-card" />
      </div>
    </div>
  );
}

function renderPatientView(
  patientId: string,
  currentTab: string,
  setCurrentTab: (tab: string) => void,
  patient: any,
  error: any,
  isLoading: boolean,
  genomicsData: import("./api/types").GenomicData | undefined,
  genomicsError: string | null,
  genomicsLoading: boolean
) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="text-center p-8">
        <h2 className="text-2xl font-bold text-destructive">Patient Not Found</h2>
        <p className="text-muted-foreground mt-2">Unable to load patient data.</p>
      </div>
    );
  }

  const headerData = transformPatientToHeader(patient);
  const vitalsData = transformToVitals(patient);
  const riskFactorsData = transformToRiskFactors(patient);
  const medicalHistoryData = transformToMedicalHistory(patient);
  const imagingData = transformToImagingData(patient);

  return (
    <div className="space-y-6">
      <PatientHeader patient={headerData} />
      
      <Tabs value={currentTab} onValueChange={setCurrentTab} className="patient-tabs-shell">
        <TabsList className="view-tabs-list view-tabs-scroll patient-tabs-list w-full justify-start">
          <TabsTrigger value="vitals">Vital Signs</TabsTrigger>
          <TabsTrigger value="risk">Risk Factors</TabsTrigger>
          <TabsTrigger value="history">Medical History</TabsTrigger>
          <TabsTrigger value="sample">Sample</TabsTrigger>
          <TabsTrigger value="genomics">Genomics</TabsTrigger>
          <TabsTrigger value="imaging">Imaging</TabsTrigger>
        </TabsList>
        
        <TabsContent value="vitals" className="patient-tab-panel">
          {vitalsData.hasData ? (
            <VitalSigns vitals={vitalsData} />
          ) : (
            <DataNotAvailable 
              title="Vital Signs Data Not Available" 
              message="No vital signs recorded for this patient yet."
              type="empty-for-patient"
            />
          )}
        </TabsContent>
        
        <TabsContent value="risk" className="patient-tab-panel">
          {riskFactorsData.hasData ? (
            <RiskFactors riskFactors={riskFactorsData} />
          ) : (
            <DataNotAvailable 
              title="Risk Factors Data Not Available" 
              message="No risk factor information recorded for this patient."
              type="empty-for-patient"
            />
          )}
        </TabsContent>
        
        <TabsContent value="history" className="patient-tab-panel">
          {medicalHistoryData.hasData ? (
            <MedicalHistory history={medicalHistoryData} />
          ) : (
            <DataNotAvailable 
              title="Medical History Not Available" 
              message="No medical history recorded for this patient."
              type="empty-for-patient"
            />
          )}
        </TabsContent>

        <TabsContent value="sample" className="patient-tab-panel">
          <SampleData
            patientId={patient.dna_id}
            enrollmentDate={patient.enrollment_date}
            genomicData={genomicsData}
          />
        </TabsContent>

        <TabsContent value="genomics" className="patient-tab-panel">
          {genomicsLoading ? (
            <div className="flex items-center justify-center h-64">
              <p className="text-muted-foreground">Loading genomic data...</p>
            </div>
          ) : genomicsError || !genomicsData || (genomicsData.variants.length === 0 && genomicsData.pharmacogenomics.length === 0) ? (
            <DataNotAvailable 
              title="Genomic Data Not Available" 
              message="No genomic variants have been ingested for this patient. Import VCFs to enable genomic insights."
              type="empty-for-patient"
            />
          ) : (
            <GenomicData genomicData={genomicsData} />
          )}
        </TabsContent>
        
        <TabsContent value="imaging" className="patient-tab-panel">
          {imagingData.hasData ? (
            <TraditionalImaging imaging={imagingData} />
          ) : (
            <DataNotAvailable 
              title="Imaging Data Not Available" 
              message="No echocardiogram or MRI data recorded for this patient, or imaging was marked as missing."
              type="empty-for-patient"
            />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
