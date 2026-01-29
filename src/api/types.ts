// Patient-related types
export interface Patient {
  id: number;
  dna_id: string;
  age: number | null;
  gender: string | null;
  nationality: string | null;
  enrollment_date: string | null;
  current_city: string | null;
  heart_rate: number | null;
  systolic_bp: number | null;
  diastolic_bp: number | null;
  bmi: number | null;
  hba1c: number | null;
  echo_ef: number | null;
  mri_ef: number | null;
  current_city_category: string | null;
  has_mri: boolean;
  has_echo: boolean;
  data_completeness: number;
}

export interface PatientDetail extends Patient {
  date_of_birth: string | null;
  is_pregnant: boolean;
  father_city_origin: string | null;
  childhood_city: string | null;
  consent_obtained: boolean;
  lifestyle: LifestyleData | null;
  exclusion: ExclusionCriteria | null;
  family: FamilyHistory | null;
  medical: MedicalHistory | null;
  physical: PhysicalExam | null;
  labs: LabResults | null;
  ecg: EcgData | null;
  echo: EchoData | null;
  mri: MriData | null;
  geographic: GeographicData | null;
}

export interface LifestyleData {
  current_smoker: boolean;
  smoking_duration: string | null;
  cigarettes_per_day: number | null;
  drinks_alcohol: boolean;
  takes_medication: boolean;
  ever_smoked: boolean;
  smoking_years: number | null;
}

export interface ExclusionCriteria {
  under_18: boolean;
  non_egyptian_parents: boolean;
  known_cvs_disease: boolean;
  known_collagen_disease: boolean;
  communication_difficulties: boolean;
  unwilling_to_participate: boolean;
  pregnant_female: boolean;
  contraindications_mri: boolean;
  history_sudden_death: boolean;
  history_familial_cardiomyopathies: boolean;
  history_premature_cad: boolean;
}

export interface FamilyHistory {
  consanguinous_marriage_offspring: boolean;
  parents_occupation: string | null;
  marital_status: string | null;
  consanguinous_marriage: boolean;
  number_of_children: number | null;
  siblings_count: number | null;
  is_twin_or_triplet: boolean;
  family_disease_info: string | null;
  non_cardiac_condition_family: boolean;
  non_cardiac_condition_details: string | null;
  childhood_location: string | null;
}

export interface MedicalHistory {
  heart_attack_or_angina: boolean;
  high_blood_pressure: boolean;
  dyslipidemia: boolean;
  rheumatic_fever: boolean;
  anaemia: boolean;
  lung_problems: boolean;
  kidney_problems: boolean;
  liver_problems: boolean;
  diabetes_mellitus: boolean;
  prior_heart_failure: boolean;
  neurological_problems: boolean;
  musculoskeletal_problems: boolean;
  autoimmune_problems: boolean;
  undergone_surgery: boolean;
  procedure_details: string | null;
  malignancy: boolean;
  comorbidity: number;
}

export interface PhysicalExam {
  examination_date: string | null;
  examination_type: string | null;
  heart_rate: number | null;
  regularity: string | null;
  bp_reading: string | null;
  systolic_bp: number | null;
  diastolic_bp: number | null;
  height_cm: number | null;
  weight_kg: number | null;
  bmi: number | null;
  bsa: number | null;
  jvp: number | null;
  abnormal_physical_structure: boolean;
  s1: string | null;
  s2: string | null;
  s3: boolean;
  s4: boolean;
}

export interface LabResults {
  hba1c: number | null;
  troponin_i: number | null;
  hba1c_outlier: boolean;
  troponin_outlier: boolean;
  heart_rate_outlier: boolean;
}

export interface EcgData {
  rate: number | null;
  rate_clean: number | null;
  rhythm: string | null;
  p_wave_abnormality: boolean;
  pr_interval: number | null;
  qrs_duration: number | null;
  qrs_abnormalities: boolean;
  st_segment_abnormalities: boolean;
  qtc_interval: number | null;
  t_wave_abnormalities: boolean;
  ecg_conclusion: string | null;
  missing_ecg: boolean;
}

export interface EchoData {
  echo_date: string | null;
  aortic_root: number | null;
  left_atrium: number | null;
  right_ventricle: number | null;
  lvedd: number | null;
  lvesd: number | null;
  ivsd: number | null;
  ivss: number | null;
  lvpwd: number | null;
  lvpws: number | null;
  ef: number | null;
  fs: number | null;
  subaortic_membrane: boolean;
  mitral_regurge: string | null;
  mitral_stenosis: boolean;
  tricuspid_regurge: string | null;
  tricuspid_stenosis: boolean;
  aortic_regurge: string | null;
  aortic_stenosis: boolean;
  pulmonary_regurge: string | null;
  pulmonary_stenosis: boolean;
  missing_echo: boolean;
}

export interface MriData {
  mri_performed: boolean;
  heart_rate_during_mri: number | null;
  mri_date: string | null;
  lv_ejection_fraction: number | null;
  lv_end_diastolic_volume: number | null;
  lv_end_systolic_volume: number | null;
  lv_mass: number | null;
  rv_ejection_fraction: number | null;
  missing_mri: boolean;
}

export interface GeographicData {
  current_city_category: string | null;
  childhood_city_category: string | null;
  migration_pattern: string | null;
}

// Analytics types
export interface RegistryOverview {
  totalPatients: number;
  maleCount: number;
  femaleCount: number;
  averageAge: string;
  dataCompleteness: string;
  withMri: number;
  withEcho: number;
  withBothEchoMri: number;
  withEcg: number;
}

export interface DemographicsData {
  ageGender: Array<{
    age_group: string;
    male: number;
    female: number;
  }>;
  nationality: Array<{
    nationality: string;
    count: number;
  }>;
  maritalStatus: Array<{
    marital_status: string;
    count: number;
  }>;
}

export interface ClinicalMetrics {
  bmiDistribution: Array<{ category: string; count: number }>;
  bpDistribution: Array<{ status: string; count: number }>;
  efDistribution: Array<{ category: string; count: number }>;
  hba1cDistribution: Array<{ category: string; count: number }>;
}

export interface ComorbidityData {
  conditions: {
    hypertension: number;
    diabetes: number;
    dyslipidemia: number;
    cad: number;
    heart_failure: number;
    lung_disease: number;
    kidney_disease: number;
    neurological: number;
  };
  comorbidityDistribution: Array<{ comorbidity: number; count: number }>;
}

export interface LifestyleStats {
  smoking: {
    current_smokers: number;
    former_smokers: number;
    never_smoked: number;
  };
  smokingDuration: Array<{ duration: string; count: number }>;
}

export interface GeographicStats {
  cityCategory: Array<{ current_city_category: string; count: number }>;
  migration: Array<{ migration_pattern: string; count: number }>;
  cityDistribution: Array<{ current_city: string; count: number; avg_age: number }>;
}

export interface MapData {
  region: string;
  coordinates: [number, number];
  patientCount: number;
  prevalence: number;
  demographics: {
    averageAge: number;
    genderRatio: number;
    ethnicityMix: Record<string, number>;
  };
  riskFactors: Record<string, number>;
  outcomes: {
    mortality: number;
    readmission: number;
    complications: number;
  };
}

export interface EnrollmentTrend {
  month: string;
  enrolled: number;
  cumulative: number;
}

export interface DataQuality {
  byCategory: {
    physical_exam: number;
    lab_results: number;
    ecg: number;
    echo: number;
    mri: number;
    overall: number;
  };
  distribution: Array<{ category: string; count: number }>;
}

// Cohort types
export interface CohortCriteria {
  ageMin?: number;
  ageMax?: number;
  gender?: string[];
  hasHypertension?: boolean;
  hasDiabetes?: boolean;
  hasDyslipidemia?: boolean;
  isSmoker?: boolean;
  bmiMin?: number;
  bmiMax?: number;
  efMin?: number;
  efMax?: number;
  hasEcho?: boolean;
  hasMri?: boolean;
  hasEcg?: boolean;
  minCompleteness?: number;
  cityCategory?: string[];
  migrationPattern?: string[];
}

export interface CohortQueryResult {
  patients: Patient[];
  totalCount: number;
  criteria: CohortCriteria;
}

export interface CohortSummary {
  demographics: {
    total: number;
    avg_age: number;
    min_age: number;
    max_age: number;
    male_count: number;
    female_count: number;
  };
  clinical: {
    avg_bmi: number;
    avg_sbp: number;
    avg_dbp: number;
    avg_hba1c: number;
    avg_ef: number;
  };
  conditions: {
    hypertension: number;
    diabetes: number;
    dyslipidemia: number;
  };
}

// Chart types
export interface ChartConfig {
  xAxis: string;
  yAxis?: string;
  groupBy?: string;
  chartType: 'bar' | 'line' | 'scatter' | 'pie';
  filters?: Record<string, unknown>;
}

export interface ChartField {
  id: string;
  label: string;
  table: string;
}

export interface ChartFields {
  numeric: ChartField[];
  categorical: ChartField[];
  boolean: ChartField[];
}

// Vitals types
export interface PatientVitals {
  current: {
    systolic: number | null;
    diastolic: number | null;
    heartRate: number | null;
    weight: number | null;
    height: number | null;
    bmi: number | null;
    bsa: number | null;
    hba1c: number | null;
    troponin: number | null;
  };
}

// Risk factors
export interface RiskFactors {
  dna_id: string;
  diabetes_mellitus: boolean;
  high_blood_pressure: boolean;
  dyslipidemia: boolean;
  current_smoker: boolean;
  ever_smoked: boolean;
  obese: boolean;
  heart_attack_or_angina: boolean;
  history_sudden_death: boolean;
  history_premature_cad: boolean;
  risk_score: number;
}

// Imaging data
export interface ImagingData {
  echo: EchoData | null;
  mri: MriData | null;
}
