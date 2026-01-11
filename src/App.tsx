import { useState } from "react";
import { AppProvider, useApp } from "./context/AppContext";
import { Sidebar } from "./components/Sidebar";
import { ChatInterface } from "./components/EnhancedChatInterface";
import { PatientHeader } from "./components/PatientHeader";
import { PatientSearch } from "./components/PatientSearch";
import { VitalSigns } from "./components/VitalSigns";
import { RiskFactors } from "./components/RiskFactors";
import { MedicalHistory } from "./components/MedicalHistory";
import { TraditionalImaging } from "./components/TraditionalImaging";
import { PatientRegistryTable } from "./components/PatientRegistryTable";
import { RegistryAnalytics } from "./components/RegistryAnalytics";
import { ChartBuilder } from "./components/ChartBuilder";
import { CohortBuilder } from "./components/CohortBuilder";
import { DataDictionary } from "./components/DataDictionary";
import { Settings } from "./components/Settings";
import { UserProfile } from "./components/UserProfile";
import { DataNotAvailable } from "./components/DataNotAvailable";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { usePatient } from "./hooks/usePatients";
import type { PatientDetail } from "./api/types";

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
  const hasMedicalData = patient.medical !== null;
  const hasLabsData = patient.labs !== null;
  
  const diagnoses = [];
  
  if (hasMedicalData) {
    if (patient.medical?.high_blood_pressure) {
      diagnoses.push({
        id: "D001",
        condition: "Hypertension",
        icd10Code: "I10",
        category: "Cardiovascular",
        diagnosedDate: patient.enrollment_date || "Not recorded",
        status: "treated" as const,
        severity: "Present" as const,
        clinicalNotes: "Recorded in medical history"
      });
    }
    
    if (patient.medical?.diabetes_mellitus) {
      diagnoses.push({
        id: "D002",
        condition: "Diabetes Mellitus",
        icd10Code: "E11",
        category: "Metabolic",
        diagnosedDate: patient.enrollment_date || "Not recorded",
        status: "treated" as const,
        severity: "Present" as const,
        clinicalNotes: "Recorded in medical history"
      });
    }

    if (patient.medical?.dyslipidemia) {
      diagnoses.push({
        id: "D003",
        condition: "Dyslipidemia",
        icd10Code: "E78.5",
        category: "Metabolic",
        diagnosedDate: patient.enrollment_date || "Not recorded",
        status: "treated" as const,
        severity: "Present" as const,
        clinicalNotes: "Recorded in medical history"
      });
    }

    if (patient.medical?.heart_attack_or_angina) {
      diagnoses.push({
        id: "D004",
        condition: "Coronary Heart Disease / Angina",
        icd10Code: "I25.1",
        category: "Cardiovascular",
        diagnosedDate: patient.enrollment_date || "Not recorded",
        status: "symptomatic" as const,
        severity: "Present" as const,
        clinicalNotes: "History of heart attack or angina"
      });
    }

    if (patient.medical?.prior_heart_failure) {
      diagnoses.push({
        id: "D005",
        condition: "Heart Failure",
        icd10Code: "I50",
        category: "Cardiovascular",
        diagnosedDate: patient.enrollment_date || "Not recorded",
        status: "treated" as const,
        severity: "Present" as const,
        clinicalNotes: "Prior heart failure"
      });
    }

    if (patient.medical?.rheumatic_fever) {
      diagnoses.push({
        id: "D006",
        condition: "Rheumatic Fever",
        icd10Code: "I00",
        category: "Cardiovascular",
        diagnosedDate: patient.enrollment_date || "Not recorded",
        status: "stable" as const,
        severity: "History" as const,
        clinicalNotes: "History of rheumatic fever"
      });
    }

    if (patient.medical?.anaemia) {
      diagnoses.push({
        id: "D007",
        condition: "Anaemia",
        icd10Code: "D64.9",
        category: "Hematologic",
        diagnosedDate: patient.enrollment_date || "Not recorded",
        status: "treated" as const,
        severity: "Present" as const,
        clinicalNotes: "Recorded in medical history"
      });
    }

    if (patient.medical?.kidney_problems) {
      diagnoses.push({
        id: "D008",
        condition: "Kidney Disease",
        icd10Code: "N18",
        category: "Renal",
        diagnosedDate: patient.enrollment_date || "Not recorded",
        status: "treated" as const,
        severity: "Present" as const,
        clinicalNotes: "Kidney problems recorded"
      });
    }

    if (patient.medical?.liver_problems) {
      diagnoses.push({
        id: "D009",
        condition: "Liver Disease",
        icd10Code: "K76.9",
        category: "Hepatic",
        diagnosedDate: patient.enrollment_date || "Not recorded",
        status: "treated" as const,
        severity: "Present" as const,
        clinicalNotes: "Liver problems recorded"
      });
    }
  }

  const tests = [];
  if (hasLabsData && patient.labs) {
    if (patient.labs.hba1c !== null) {
      tests.push({
        id: "T001",
        name: "HbA1c",
        date: patient.enrollment_date || "Not recorded",
        result: `${Number(patient.labs.hba1c).toFixed(1)}%`,
        status: (Number(patient.labs.hba1c) > 6.5 ? "abnormal" : "normal") as const,
        notes: patient.labs.hba1c_outlier ? "Flagged as outlier" : undefined
      });
    }
    if (patient.labs.troponin_i !== null) {
      tests.push({
        id: "T002",
        name: "Troponin I",
        date: patient.enrollment_date || "Not recorded",
        result: `${Number(patient.labs.troponin_i).toFixed(2)} ng/L`,
        status: (Number(patient.labs.troponin_i) > 14 ? "abnormal" : "normal") as const,
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
    hasData: hasEcho || hasMri,
    ct, 
    mri, 
    echo 
  };
}

export default function App() {
  const [currentView, setCurrentView] = useState("welcome");
  const [selectedPatientDnaId, setSelectedPatientDnaId] = useState<string | null>(null);
  
  const { data: patientData, isLoading: patientLoading, error: patientError } = usePatient(selectedPatientDnaId || '');

  const handlePatientSelect = (dnaId: string) => {
    setSelectedPatientDnaId(dnaId);
    setCurrentView("patient");
  };

  const renderMainContent = () => {
    switch (currentView) {
      case "welcome":
        return <ChatInterface />;
      
      case "registry":
        return <PatientRegistryTable onPatientSelect={handlePatientSelect} />;
      
      case "cohort":
        return <CohortBuilder />;
      
      case "analytics":
        return <RegistryAnalytics />;
      
      case "charts":
        return <ChartBuilder />;
      
      case "dictionary":
        return <DataDictionary />;
      
      case "settings":
        return <Settings />;
      
      case "profile":
        return <UserProfile />;
      
      case "patient":
      default:
        if (!selectedPatientDnaId) {
          return (
            <div className="space-y-6">
              <PatientSearch 
                currentMrn="" 
                onPatientSelect={handlePatientSelect} 
              />
              <div className="flex items-center justify-center h-64">
                <p className="text-muted-foreground">Select a patient from the search above or from the Patient Registry.</p>
              </div>
            </div>
          );
        }

        if (patientLoading) {
          return (
            <div className="space-y-6">
              <PatientSearch 
                currentMrn={selectedPatientDnaId} 
                onPatientSelect={handlePatientSelect} 
              />
              <div className="flex items-center justify-center h-64">
                <p className="text-muted-foreground">Loading patient data...</p>
              </div>
            </div>
          );
        }

        if (patientError || !patientData) {
          return (
            <div className="space-y-6">
              <PatientSearch 
                currentMrn={selectedPatientDnaId} 
                onPatientSelect={handlePatientSelect} 
              />
              <div className="flex items-center justify-center h-64">
                <p className="text-destructive">Error loading patient: {patientError?.message || 'Patient not found'}</p>
              </div>
            </div>
          );
        }

        const patient = patientData;
        const patientHeader = transformPatientToHeader(patient);
        const vitals = transformToVitals(patient);
        const riskFactors = transformToRiskFactors(patient);
        const medicalHistory = transformToMedicalHistory(patient);
        const imagingData = transformToImagingData(patient);

        return (
          <div className="space-y-6">
            <PatientSearch 
              currentMrn={selectedPatientDnaId} 
              onPatientSelect={handlePatientSelect} 
            />
            
            <PatientHeader patient={patientHeader} />
            
            <Tabs defaultValue="vitals" className="space-y-4">
              <TabsList className="grid w-full grid-cols-6">
                <TabsTrigger value="vitals">Vital Signs</TabsTrigger>
                <TabsTrigger value="risk">Risk Assessment</TabsTrigger>
                <TabsTrigger value="history">Medical History</TabsTrigger>
                <TabsTrigger value="genomics">Genomics</TabsTrigger>
                <TabsTrigger value="biomarkers">Biomarkers</TabsTrigger>
                <TabsTrigger value="imaging">Imaging</TabsTrigger>
              </TabsList>

              <TabsContent value="vitals">
                {vitals.hasData ? (
                  <VitalSigns vitals={vitals} />
                ) : (
                  <DataNotAvailable 
                    title="Vital Signs Data Not Available" 
                    message="No physical examination data recorded for this patient in the EHVol database."
                    type="empty-for-patient"
                  />
                )}
              </TabsContent>

              <TabsContent value="risk">
                {riskFactors.hasData ? (
                  <RiskFactors riskFactors={riskFactors} />
                ) : (
                  <DataNotAvailable 
                    title="Risk Factor Data Not Available" 
                    message="No medical history or lifestyle data recorded for this patient."
                    type="empty-for-patient"
                  />
                )}
              </TabsContent>

              <TabsContent value="history">
                {medicalHistory.hasData ? (
                  <MedicalHistory history={medicalHistory} />
                ) : (
                  <DataNotAvailable 
                    title="Medical History Not Available" 
                    message="No diagnoses or lab results recorded for this patient."
                    type="empty-for-patient"
                  />
                )}
              </TabsContent>

              <TabsContent value="genomics">
                <DataNotAvailable 
                  title="Genomic Data Not Available" 
                  message="Genomic data (polygenic risk scores, genetic variants, pharmacogenomics) is not included in the EHVol database schema."
                  type="not-in-database"
                />
              </TabsContent>

              <TabsContent value="biomarkers">
                <DataNotAvailable 
                  title="Protein Biomarkers Not Available" 
                  message="Detailed protein biomarker panels (hs-CRP, NT-proBNP, IL-6, etc.) are not included in the EHVol database schema. Only basic lab values (HbA1c, Troponin I) are available in the Medical History tab."
                  type="not-in-database"
                />
              </TabsContent>

              <TabsContent value="imaging">
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
  };

  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

function AppContent() {
  const { currentView, setCurrentView, selectedPatient, setSelectedPatient } = useApp();
  const [currentTab, setCurrentTab] = useState<string>("vitals");
  
  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar currentView={currentView} onViewChange={setCurrentView} className="flex-shrink-0" />
      
      <div className="flex-1 overflow-auto">
        <div className="p-6">
          {renderContent(currentView, selectedPatient, setSelectedPatient, currentTab, setCurrentTab)}
        </div>
      </div>
    </div>
  );
}

function renderContent(
  currentView: string,
  selectedPatient: string | null,
  setSelectedPatient: (id: string | null) => void,
  currentTab: string,
  setCurrentTab: (tab: string) => void
) {
  const renderMainContent = () => {
    switch (currentView) {
      case "welcome":
        return <ChatInterface />;
      case "registry":
        return <PatientRegistryTable onPatientClick={setSelectedPatient} />;
      case "patient":
        if (!selectedPatient) {
          return <PatientSearch onSelectPatient={setSelectedPatient} />;
        }
        return renderPatientView(selectedPatient, currentTab, setCurrentTab);
      case "analytics":
        return <RegistryAnalytics />;
      case "cohort":
        return <CohortBuilder />;
      case "charts":
        return <ChartBuilder />;
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

function renderPatientView(patientId: string, currentTab: string, setCurrentTab: (tab: string) => void) {
  const { data: patient, error, isLoading } = usePatient(patientId);

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
  const imagingData = transformToImaging(patient);

  return (
    <div className="space-y-6">
      <PatientHeader {...headerData} />
      
      <Tabs value={currentTab} onValueChange={setCurrentTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="vitals">Vital Signs</TabsTrigger>
          <TabsTrigger value="risk">Risk Factors</TabsTrigger>
          <TabsTrigger value="history">Medical History</TabsTrigger>
          <TabsTrigger value="imaging">Imaging</TabsTrigger>
        </TabsList>
        
        <TabsContent value="vitals">
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
        
        <TabsContent value="risk">
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
        
        <TabsContent value="history">
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
        
        <TabsContent value="imaging">
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
