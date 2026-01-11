import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { BookOpen, Search, Download, Filter, Info, Database, FileText, Tag, Clock, TrendingUp, Calendar, MousePointer, CheckCircle2, Shield, Link2, FileJson, ExternalLink, AlertCircle, Play, Save, User, FlaskConical, Dna, Camera, Pill, BarChart3, Heart, RefreshCw, ClipboardList } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { Label } from "./ui/label";
import { useRegistryOverview } from "../hooks/useAnalytics";

interface DataVariable {
  id: string;
  name: string;
  description: string;
  category: string;
  temporalCategory: 'baseline' | 'longitudinal' | 'repeated-measures' | 'event-driven';
  measurementFrequency?: string;
  validComparisonTimeframe?: string;
  dataType: string;
  units?: string;
  referenceRange?: string;
  validValues?: string[];
  source: string;
  lastUpdated: string;
  completeness: number;
  quality: 'high' | 'medium' | 'low';
  requiredField: boolean;
  derivedFrom?: string[];
  clinicalSignificance?: string;
  methodology?: string;
  limitations?: string;
  temporalConsiderations?: string;
}

export function DataDictionary() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedTemporalCategory, setSelectedTemporalCategory] = useState("all");
  const [selectedVariable, setSelectedVariable] = useState<DataVariable | null>(null);
  const [filterQuality, setFilterQuality] = useState("all");
  
  // Fetch real patient count from API
  const { data: overview } = useRegistryOverview();
  const patientCount = overview?.totalPatients?.toLocaleString() ?? '...';

  // EHVol Database Variables - Based on actual database schema
  const dataVariables: DataVariable[] = [
    // Demographics
    {
      id: "dna_id",
      name: "DNA ID",
      description: "Unique patient identifier in the EHVol registry",
      category: "Demographics",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable - identifier",
      dataType: "String",
      source: "EHVol Registry",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: true,
      clinicalSignificance: "Primary key for patient identification and data linkage."
    },
    {
      id: "date_of_birth",
      name: "Date of Birth",
      description: "Patient date of birth",
      category: "Demographics",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable - baseline only",
      dataType: "Date",
      source: "Patient Registration",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: true
    },
    {
      id: "age",
      name: "Age at Enrollment",
      description: "Patient age at time of enrollment in years",
      category: "Demographics",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable - baseline only",
      dataType: "Numeric",
      units: "years",
      referenceRange: "18-100",
      source: "Calculated from date of birth",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: true,
      clinicalSignificance: "Primary risk factor for cardiovascular disease."
    },
    {
      id: "gender",
      name: "Gender",
      description: "Patient biological sex",
      category: "Demographics",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Categorical",
      validValues: ["Male", "Female"],
      source: "Patient Registration",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: true
    },
    {
      id: "nationality",
      name: "Nationality",
      description: "Patient nationality (Egyptian cohort)",
      category: "Demographics",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Categorical",
      validValues: ["Egyptian"],
      source: "Patient Registration",
      lastUpdated: "2024-12-15",
      completeness: 99,
      quality: "high",
      requiredField: false
    },
    {
      id: "enrollment_date",
      name: "Date of Enrollment",
      description: "Date when patient was enrolled in the EHVol study",
      category: "Demographics",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Reference point for all follow-up",
      dataType: "Date",
      source: "EHVol Registry",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: true
    },
    {
      id: "current_city",
      name: "Current City of Residence",
      description: "Patient's current city of residence",
      category: "Demographics",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "String",
      source: "Patient Registration",
      lastUpdated: "2024-12-15",
      completeness: 98,
      quality: "high",
      requiredField: false
    },
    {
      id: "current_city_category",
      name: "City Category",
      description: "Classification of residence (Rural/Urban/Town)",
      category: "Demographics",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Categorical",
      validValues: ["Rural", "Urban", "Town/City"],
      source: "Derived from current city",
      lastUpdated: "2024-12-15",
      completeness: 98,
      quality: "high",
      requiredField: false,
      derivedFrom: ["current_city"]
    },
    {
      id: "childhood_city_category",
      name: "Childhood City Category",
      description: "Classification of childhood residence location",
      category: "Demographics",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Categorical",
      validValues: ["Rural", "Urban", "Village/Countryside", "Town/City"],
      source: "Patient Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 95,
      quality: "medium",
      requiredField: false
    },
    {
      id: "migration_pattern",
      name: "Migration Pattern",
      description: "Pattern of geographic migration from childhood to current residence",
      category: "Demographics",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Categorical",
      validValues: ["Rural - Rural", "Rural - Urban", "Urban - Urban", "Urban - Rural"],
      source: "Derived from childhood and current city",
      lastUpdated: "2024-12-15",
      completeness: 93,
      quality: "medium",
      requiredField: false,
      derivedFrom: ["current_city_category", "childhood_city_category"]
    },
    // Lifestyle
    {
      id: "current_smoker",
      name: "Current Smoker",
      description: "Whether patient currently smokes (within past year)",
      category: "Lifestyle",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Patient Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 98,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Major modifiable cardiovascular risk factor."
    },
    {
      id: "ever_smoked",
      name: "Ever Smoked",
      description: "Whether patient has ever smoked in their lifetime",
      category: "Lifestyle",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Patient Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 98,
      quality: "high",
      requiredField: false
    },
    {
      id: "smoking_years",
      name: "Smoking Duration",
      description: "Number of years patient has smoked",
      category: "Lifestyle",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "years",
      source: "Patient Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 45,
      quality: "medium",
      requiredField: false,
      limitations: "Only collected for smokers/ex-smokers"
    },
    {
      id: "cigarettes_per_day",
      name: "Cigarettes Per Day",
      description: "Average number of cigarettes smoked per day",
      category: "Lifestyle",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "cigarettes/day",
      source: "Patient Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 30,
      quality: "medium",
      requiredField: false,
      limitations: "Only collected for current smokers"
    },
    {
      id: "drinks_alcohol",
      name: "Alcohol Consumption",
      description: "Whether patient consumes alcohol",
      category: "Lifestyle",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Patient Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 98,
      quality: "high",
      requiredField: false
    },
    {
      id: "takes_medication",
      name: "Takes Medication",
      description: "Whether patient currently takes any medication",
      category: "Lifestyle",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Patient Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 98,
      quality: "high",
      requiredField: false
    },
    // Medical History
    {
      id: "high_blood_pressure",
      name: "Hypertension",
      description: "History of high blood pressure diagnosis",
      category: "Medical History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Medical History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Major cardiovascular risk factor. Strong predictor of stroke and heart disease."
    },
    {
      id: "diabetes_mellitus",
      name: "Diabetes Mellitus",
      description: "History of diabetes mellitus diagnosis",
      category: "Medical History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Medical History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Major cardiovascular risk factor. Associated with accelerated atherosclerosis."
    },
    {
      id: "dyslipidemia",
      name: "Dyslipidemia",
      description: "History of abnormal lipid levels",
      category: "Medical History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Medical History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Treatable cardiovascular risk factor."
    },
    {
      id: "heart_attack_or_angina",
      name: "Heart Attack or Angina",
      description: "History of myocardial infarction or angina pectoris",
      category: "Medical History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Medical History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Indicates established coronary artery disease. High-risk category."
    },
    {
      id: "prior_heart_failure",
      name: "Prior Heart Failure",
      description: "History of heart failure diagnosis",
      category: "Medical History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Medical History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Indicates significant cardiac dysfunction. High-risk category."
    },
    {
      id: "rheumatic_fever",
      name: "Rheumatic Fever",
      description: "History of rheumatic fever",
      category: "Medical History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Medical History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Can cause rheumatic heart disease with valvular involvement."
    },
    {
      id: "anaemia",
      name: "Anaemia",
      description: "History of anaemia diagnosis",
      category: "Medical History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Medical History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false
    },
    {
      id: "kidney_problems",
      name: "Kidney Problems",
      description: "History of kidney disease or dysfunction",
      category: "Medical History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Medical History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Chronic kidney disease is a cardiovascular risk equivalent."
    },
    {
      id: "liver_problems",
      name: "Liver Problems",
      description: "History of liver disease or dysfunction",
      category: "Medical History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Medical History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false
    },
    {
      id: "lung_problems",
      name: "Lung Problems",
      description: "History of pulmonary disease",
      category: "Medical History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Medical History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false
    },
    {
      id: "neurological_problems",
      name: "Neurological Problems",
      description: "History of neurological conditions",
      category: "Medical History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Medical History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false
    },
    {
      id: "autoimmune_problems",
      name: "Autoimmune Problems",
      description: "History of autoimmune conditions",
      category: "Medical History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Medical History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false
    },
    {
      id: "malignancy",
      name: "Malignancy",
      description: "History of cancer diagnosis",
      category: "Medical History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Medical History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false
    },
    {
      id: "comorbidity",
      name: "Comorbidity Count",
      description: "Total number of comorbid conditions",
      category: "Medical History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      source: "Calculated from medical history",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false,
      derivedFrom: ["high_blood_pressure", "diabetes_mellitus", "dyslipidemia", "heart_attack_or_angina", "prior_heart_failure"]
    },
    // Family History
    {
      id: "consanguinous_marriage",
      name: "Consanguineous Marriage",
      description: "Whether patient's parents were related",
      category: "Family History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Family History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 95,
      quality: "medium",
      requiredField: false,
      clinicalSignificance: "Relevant for genetic disease risk assessment in Egyptian population."
    },
    {
      id: "family_disease_info",
      name: "Family Disease History",
      description: "Details of diseases running in the family",
      category: "Family History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "String",
      source: "Family History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 60,
      quality: "medium",
      requiredField: false,
      limitations: "Free text field with variable detail"
    },
    {
      id: "siblings_count",
      name: "Number of Siblings",
      description: "Total number of siblings",
      category: "Family History",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      source: "Family History Questionnaire",
      lastUpdated: "2024-12-15",
      completeness: 95,
      quality: "high",
      requiredField: false
    },
    // Physical Examination
    {
      id: "heart_rate",
      name: "Heart Rate",
      description: "Resting heart rate at physical examination",
      category: "Physical Examination",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Compare with other baseline vitals",
      dataType: "Numeric",
      units: "bpm",
      referenceRange: "60-100 bpm",
      source: "Physical Examination",
      lastUpdated: "2024-12-15",
      completeness: 98,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Elevated resting heart rate associated with increased cardiovascular mortality."
    },
    {
      id: "systolic_bp",
      name: "Systolic Blood Pressure",
      description: "Systolic blood pressure measurement",
      category: "Physical Examination",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Compare with other baseline measurements",
      dataType: "Numeric",
      units: "mmHg",
      referenceRange: "<120 mmHg (optimal)",
      source: "Physical Examination",
      lastUpdated: "2024-12-15",
      completeness: 98,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Key indicator of hypertension and cardiovascular risk."
    },
    {
      id: "diastolic_bp",
      name: "Diastolic Blood Pressure",
      description: "Diastolic blood pressure measurement",
      category: "Physical Examination",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Compare with other baseline measurements",
      dataType: "Numeric",
      units: "mmHg",
      referenceRange: "<80 mmHg (optimal)",
      source: "Physical Examination",
      lastUpdated: "2024-12-15",
      completeness: 98,
      quality: "high",
      requiredField: false
    },
    {
      id: "height_cm",
      name: "Height",
      description: "Patient height in centimeters",
      category: "Physical Examination",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "cm",
      referenceRange: "140-200 cm",
      source: "Physical Examination",
      lastUpdated: "2024-12-15",
      completeness: 98,
      quality: "high",
      requiredField: false
    },
    {
      id: "weight_kg",
      name: "Weight",
      description: "Patient weight in kilograms",
      category: "Physical Examination",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "kg",
      referenceRange: "40-150 kg",
      source: "Physical Examination",
      lastUpdated: "2024-12-15",
      completeness: 98,
      quality: "high",
      requiredField: false
    },
    {
      id: "bmi",
      name: "Body Mass Index",
      description: "Body mass index calculated from height and weight",
      category: "Physical Examination",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "kg/m²",
      referenceRange: "18.5-24.9 (normal)",
      source: "Calculated from height and weight",
      lastUpdated: "2024-12-15",
      completeness: 98,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "BMI ≥30 indicates obesity, a major cardiovascular risk factor.",
      derivedFrom: ["height_cm", "weight_kg"]
    },
    {
      id: "bsa",
      name: "Body Surface Area",
      description: "Body surface area calculated using DuBois formula",
      category: "Physical Examination",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "m²",
      referenceRange: "1.5-2.5 m²",
      source: "Calculated from height and weight",
      lastUpdated: "2024-12-15",
      completeness: 98,
      quality: "high",
      requiredField: false,
      derivedFrom: ["height_cm", "weight_kg"]
    },
    {
      id: "jvp",
      name: "Jugular Venous Pressure",
      description: "Jugular venous pressure measurement",
      category: "Physical Examination",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "cm H₂O",
      referenceRange: "<8 cm H₂O",
      source: "Physical Examination",
      lastUpdated: "2024-12-15",
      completeness: 85,
      quality: "medium",
      requiredField: false,
      clinicalSignificance: "Elevated JVP suggests right heart failure or fluid overload."
    },
    // Laboratory Results
    {
      id: "hba1c",
      name: "HbA1c",
      description: "Glycated hemoglobin level indicating average blood glucose",
      category: "Laboratory",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Reflects 2-3 month glucose average",
      dataType: "Numeric",
      units: "%",
      referenceRange: "<5.7% (normal), 5.7-6.4% (prediabetes), ≥6.5% (diabetes)",
      source: "Laboratory Results",
      lastUpdated: "2024-12-15",
      completeness: 85,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Gold standard for diabetes diagnosis and glycemic control assessment."
    },
    {
      id: "troponin_i",
      name: "Troponin I",
      description: "Cardiac troponin I biomarker level",
      category: "Laboratory",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Compare with reference range",
      dataType: "Numeric",
      units: "ng/L",
      referenceRange: "<14 ng/L (normal)",
      source: "Laboratory Results",
      lastUpdated: "2024-12-15",
      completeness: 80,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Cardiac injury marker. Elevated levels indicate myocardial damage."
    },
    // ECG
    {
      id: "ecg_rate",
      name: "ECG Heart Rate",
      description: "Heart rate measured from ECG",
      category: "ECG",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Compare with clinical heart rate",
      dataType: "Numeric",
      units: "bpm",
      referenceRange: "60-100 bpm",
      source: "12-Lead ECG",
      lastUpdated: "2024-12-15",
      completeness: 92,
      quality: "high",
      requiredField: false
    },
    {
      id: "ecg_rhythm",
      name: "ECG Rhythm",
      description: "Cardiac rhythm classification from ECG",
      category: "ECG",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Categorical",
      validValues: ["regular", "irregular", "sinus", "atrial fibrillation"],
      source: "12-Lead ECG",
      lastUpdated: "2024-12-15",
      completeness: 92,
      quality: "high",
      requiredField: false
    },
    {
      id: "pr_interval",
      name: "PR Interval",
      description: "PR interval duration on ECG",
      category: "ECG",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "ms",
      referenceRange: "120-200 ms",
      source: "12-Lead ECG",
      lastUpdated: "2024-12-15",
      completeness: 90,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Prolonged PR suggests AV conduction delay."
    },
    {
      id: "qrs_duration",
      name: "QRS Duration",
      description: "QRS complex duration on ECG",
      category: "ECG",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "ms",
      referenceRange: "<120 ms",
      source: "12-Lead ECG",
      lastUpdated: "2024-12-15",
      completeness: 90,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Wide QRS suggests bundle branch block or ventricular conduction delay."
    },
    {
      id: "qtc_interval",
      name: "Corrected QT Interval",
      description: "Heart rate-corrected QT interval",
      category: "ECG",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "ms",
      referenceRange: "<450 ms (men), <460 ms (women)",
      source: "12-Lead ECG",
      lastUpdated: "2024-12-15",
      completeness: 90,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Prolonged QTc associated with increased arrhythmia risk."
    },
    {
      id: "ecg_conclusion",
      name: "ECG Conclusion",
      description: "Overall ECG interpretation summary",
      category: "ECG",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "String",
      source: "12-Lead ECG Interpretation",
      lastUpdated: "2024-12-15",
      completeness: 92,
      quality: "high",
      requiredField: false
    },
    {
      id: "missing_ecg",
      name: "Missing ECG",
      description: "Flag indicating ECG data is not available",
      category: "ECG",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Data Quality",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false
    },
    // Echocardiography
    {
      id: "echo_ef",
      name: "Ejection Fraction (Echo)",
      description: "Left ventricular ejection fraction by echocardiography",
      category: "Echocardiography",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Compare with MRI EF (note methodology differences)",
      dataType: "Numeric",
      units: "%",
      referenceRange: "55-70% (normal)",
      source: "2D Echocardiography",
      lastUpdated: "2024-12-15",
      completeness: 88,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Primary measure of left ventricular systolic function."
    },
    {
      id: "echo_fs",
      name: "Fractional Shortening",
      description: "Left ventricular fractional shortening",
      category: "Echocardiography",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "%",
      referenceRange: "25-45%",
      source: "2D Echocardiography",
      lastUpdated: "2024-12-15",
      completeness: 88,
      quality: "high",
      requiredField: false
    },
    {
      id: "lvedd",
      name: "LV End-Diastolic Diameter",
      description: "Left ventricular internal diameter at end-diastole",
      category: "Echocardiography",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Index to BSA for comparison",
      dataType: "Numeric",
      units: "mm",
      referenceRange: "39-53 mm (men), 35-51 mm (women)",
      source: "2D Echocardiography",
      lastUpdated: "2024-12-15",
      completeness: 88,
      quality: "high",
      requiredField: false
    },
    {
      id: "lvesd",
      name: "LV End-Systolic Diameter",
      description: "Left ventricular internal diameter at end-systole",
      category: "Echocardiography",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "mm",
      referenceRange: "21-35 mm",
      source: "2D Echocardiography",
      lastUpdated: "2024-12-15",
      completeness: 88,
      quality: "high",
      requiredField: false
    },
    {
      id: "left_atrium",
      name: "Left Atrium Size",
      description: "Left atrial diameter",
      category: "Echocardiography",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "cm",
      referenceRange: "2.0-4.0 cm",
      source: "2D Echocardiography",
      lastUpdated: "2024-12-15",
      completeness: 85,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "LA enlargement associated with atrial fibrillation and diastolic dysfunction."
    },
    {
      id: "aortic_root",
      name: "Aortic Root Diameter",
      description: "Aortic root diameter at sinuses of Valsalva",
      category: "Echocardiography",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "cm",
      referenceRange: "2.0-3.7 cm",
      source: "2D Echocardiography",
      lastUpdated: "2024-12-15",
      completeness: 88,
      quality: "high",
      requiredField: false
    },
    {
      id: "right_ventricle",
      name: "Right Ventricle Size",
      description: "Right ventricular basal diameter",
      category: "Echocardiography",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "mm",
      referenceRange: "20-35 mm",
      source: "2D Echocardiography",
      lastUpdated: "2024-12-15",
      completeness: 85,
      quality: "high",
      requiredField: false
    },
    {
      id: "mitral_regurge",
      name: "Mitral Regurgitation",
      description: "Severity of mitral valve regurgitation",
      category: "Echocardiography",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Categorical",
      validValues: ["None", "Trivial", "Mild", "Moderate", "Severe"],
      source: "2D Echocardiography",
      lastUpdated: "2024-12-15",
      completeness: 88,
      quality: "high",
      requiredField: false
    },
    {
      id: "aortic_regurge",
      name: "Aortic Regurgitation",
      description: "Severity of aortic valve regurgitation",
      category: "Echocardiography",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Categorical",
      validValues: ["None", "Trivial", "Mild", "Moderate", "Severe"],
      source: "2D Echocardiography",
      lastUpdated: "2024-12-15",
      completeness: 88,
      quality: "high",
      requiredField: false
    },
    {
      id: "tricuspid_regurge",
      name: "Tricuspid Regurgitation",
      description: "Severity of tricuspid valve regurgitation",
      category: "Echocardiography",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Categorical",
      validValues: ["None", "Trivial", "Mild", "Moderate", "Severe"],
      source: "2D Echocardiography",
      lastUpdated: "2024-12-15",
      completeness: 88,
      quality: "high",
      requiredField: false
    },
    {
      id: "missing_echo",
      name: "Missing Echo",
      description: "Flag indicating echocardiogram data is not available",
      category: "Echocardiography",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Data Quality",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false
    },
    // Cardiac MRI
    {
      id: "mri_performed",
      name: "MRI Performed",
      description: "Whether cardiac MRI was performed",
      category: "Cardiac MRI",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Cardiac MRI",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false
    },
    {
      id: "lv_ejection_fraction",
      name: "LV Ejection Fraction (MRI)",
      description: "Left ventricular ejection fraction by cardiac MRI",
      category: "Cardiac MRI",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Gold standard - compare with echo EF",
      dataType: "Numeric",
      units: "%",
      referenceRange: "58-74% (normal by MRI)",
      source: "Cardiac MRI",
      lastUpdated: "2024-12-15",
      completeness: 75,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Gold standard for LV function assessment. More accurate than echo."
    },
    {
      id: "rv_ejection_fraction",
      name: "RV Ejection Fraction (MRI)",
      description: "Right ventricular ejection fraction by cardiac MRI",
      category: "Cardiac MRI",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "%",
      referenceRange: "45-75%",
      source: "Cardiac MRI",
      lastUpdated: "2024-12-15",
      completeness: 70,
      quality: "high",
      requiredField: false
    },
    {
      id: "lv_end_diastolic_volume",
      name: "LV End-Diastolic Volume",
      description: "Left ventricular volume at end-diastole by MRI",
      category: "Cardiac MRI",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Index to BSA for comparison",
      dataType: "Numeric",
      units: "mL",
      referenceRange: "77-195 mL (men), 52-141 mL (women)",
      source: "Cardiac MRI",
      lastUpdated: "2024-12-15",
      completeness: 75,
      quality: "high",
      requiredField: false
    },
    {
      id: "lv_end_systolic_volume",
      name: "LV End-Systolic Volume",
      description: "Left ventricular volume at end-systole by MRI",
      category: "Cardiac MRI",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "mL",
      referenceRange: "19-72 mL (men), 13-51 mL (women)",
      source: "Cardiac MRI",
      lastUpdated: "2024-12-15",
      completeness: 75,
      quality: "high",
      requiredField: false
    },
    {
      id: "lv_mass",
      name: "LV Mass",
      description: "Left ventricular mass by cardiac MRI",
      category: "Cardiac MRI",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Index to BSA for comparison",
      dataType: "Numeric",
      units: "g",
      referenceRange: "66-150 g (men), 44-102 g (women)",
      source: "Cardiac MRI",
      lastUpdated: "2024-12-15",
      completeness: 75,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "LV hypertrophy is an independent predictor of cardiovascular events."
    },
    {
      id: "missing_mri",
      name: "Missing MRI",
      description: "Flag indicating cardiac MRI data is not available",
      category: "Cardiac MRI",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Data Quality",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false
    },
    // Quality Flags
    {
      id: "hba1c_outlier",
      name: "HbA1c Outlier Flag",
      description: "Statistical outlier flag for HbA1c value",
      category: "Data Quality",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Statistical Analysis",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false,
      derivedFrom: ["hba1c"]
    },
    {
      id: "troponin_outlier",
      name: "Troponin Outlier Flag",
      description: "Statistical outlier flag for Troponin I value",
      category: "Data Quality",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Statistical Analysis",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false,
      derivedFrom: ["troponin_i"]
    },
    {
      id: "heart_rate_outlier",
      name: "Heart Rate Outlier Flag",
      description: "Statistical outlier flag for heart rate value",
      category: "Data Quality",
      temporalCategory: "baseline",
      measurementFrequency: "Once at enrollment",
      validComparisonTimeframe: "Not applicable",
      dataType: "Boolean",
      source: "Statistical Analysis",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false,
      derivedFrom: ["heart_rate"]
    },
    {
      id: "data_completeness",
      name: "Data Completeness Score",
      description: "Overall percentage of non-missing data fields for patient",
      category: "Data Quality",
      temporalCategory: "baseline",
      measurementFrequency: "Calculated",
      validComparisonTimeframe: "Not applicable",
      dataType: "Numeric",
      units: "%",
      referenceRange: "0-100%",
      source: "Calculated from all fields",
      lastUpdated: "2024-12-15",
      completeness: 100,
      quality: "high",
      requiredField: false,
      clinicalSignificance: "Indicates reliability of patient record for analysis."
    }
  ];

  const categories = ["all", ...Array.from(new Set(dataVariables.map(v => v.category)))];
  const temporalCategories = ["all", ...Array.from(new Set(dataVariables.map(v => v.temporalCategory)))];

  const filteredVariables = dataVariables.filter(variable => {
    const matchesSearch = variable.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         variable.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === "all" || variable.category === selectedCategory;
    const matchesTemporal = selectedTemporalCategory === "all" || variable.temporalCategory === selectedTemporalCategory;
    const matchesQuality = filterQuality === "all" || variable.quality === filterQuality;
    
    return matchesSearch && matchesCategory && matchesTemporal && matchesQuality;
  });

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'high': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTemporalColor = (temporal: string) => {
    switch (temporal) {
      case 'baseline': return 'bg-blue-100 text-blue-800';
      case 'longitudinal': return 'bg-green-100 text-green-800';
      case 'repeated-measures': return 'bg-purple-100 text-purple-800';
      case 'event-driven': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTemporalIcon = (temporal: string) => {
    switch (temporal) {
      case 'baseline': return <Calendar className="h-3 w-3" />;
      case 'longitudinal': return <TrendingUp className="h-3 w-3" />;
      case 'repeated-measures': return <Clock className="h-3 w-3" />;
      case 'event-driven': return <FileText className="h-3 w-3" />;
      default: return <Info className="h-3 w-3" />;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'Demographics': return <User className="h-4 w-4 text-blue-600" />;
      case 'Lifestyle': return <Heart className="h-4 w-4 text-pink-600" />;
      case 'Medical History': return <ClipboardList className="h-4 w-4 text-red-600" />;
      case 'Family History': return <User className="h-4 w-4 text-purple-600" />;
      case 'Physical Examination': return <Heart className="h-4 w-4 text-orange-600" />;
      case 'Laboratory': return <FlaskConical className="h-4 w-4 text-green-600" />;
      case 'ECG': return <TrendingUp className="h-4 w-4 text-indigo-600" />;
      case 'Echocardiography': return <Camera className="h-4 w-4 text-cyan-600" />;
      case 'Cardiac MRI': return <Camera className="h-4 w-4 text-violet-600" />;
      case 'Data Quality': return <Shield className="h-4 w-4 text-gray-600" />;
      default: return <Database className="h-4 w-4 text-gray-600" />;
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BookOpen className="h-5 w-5" />
            <span>EHVol Registry Data Dictionary</span>
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Complete metadata catalog for the Egyptian Heart Volume (EHVol) cardiovascular research registry - {patientCount} patients with demographics, clinical, imaging, and laboratory data
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search variables..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger>
                <SelectValue placeholder="All categories" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((category) => (
                  <SelectItem key={category} value={category}>
                    {category === "all" ? "All Categories" : category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedTemporalCategory} onValueChange={setSelectedTemporalCategory}>
              <SelectTrigger>
                <SelectValue placeholder="All temporal types" />
              </SelectTrigger>
              <SelectContent>
                {temporalCategories.map((temporal) => (
                  <SelectItem key={temporal} value={temporal}>
                    {temporal === "all" ? "All Temporal Types" : temporal.charAt(0).toUpperCase() + temporal.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={filterQuality} onValueChange={setFilterQuality}>
              <SelectTrigger>
                <SelectValue placeholder="All quality levels" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Quality Levels</SelectItem>
                <SelectItem value="high">High Quality</SelectItem>
                <SelectItem value="medium">Medium Quality</SelectItem>
                <SelectItem value="low">Low Quality</SelectItem>
              </SelectContent>
            </Select>

            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export Dictionary
            </Button>
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Showing {filteredVariables.length} of {dataVariables.length} variables
            </p>
            <div className="flex space-x-2">
              <Badge variant="outline">{dataVariables.filter(v => v.temporalCategory === 'baseline').length} Baseline</Badge>
              <Badge variant="outline">{dataVariables.filter(v => v.temporalCategory === 'repeated-measures').length} Repeated</Badge>
              <Badge variant="outline">{dataVariables.filter(v => v.quality === 'high').length} High Quality</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Temporal Organization Guide */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center space-x-2">
            <Clock className="h-5 w-5" />
            <span>Temporal Data Organization Guide</span>
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Understanding temporal categories for valid longitudinal analysis
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-3 border rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Calendar className="h-4 w-4 text-blue-600" />
                <span className="font-medium text-blue-600">Baseline</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Single measurement at enrollment. Use for cross-sectional analysis and baseline adjustment.
              </p>
            </div>
            
            <div className="p-3 border rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <TrendingUp className="h-4 w-4 text-green-600" />
                <span className="font-medium text-green-600">Longitudinal</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Time-to-event or continuously changing variables. Use survival analysis methods.
              </p>
            </div>
            
            <div className="p-3 border rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Clock className="h-4 w-4 text-purple-600" />
                <span className="font-medium text-purple-600">Repeated Measures</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Regular interval measurements. Compare only matching time points for validity.
              </p>
            </div>
            
            <div className="p-3 border rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <FileText className="h-4 w-4 text-orange-600" />
                <span className="font-medium text-orange-600">Event-Driven</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Measured when clinically indicated. Group by clinical context for analysis.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Variables List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base flex items-center space-x-2">
              <MousePointer className="h-4 w-4" />
              <span>Clickable Variable Catalog</span>
            </CardTitle>
            <p className="text-xs text-muted-foreground">Click any variable row for detailed information</p>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Variable</TableHead>
                  <TableHead>Temporal Type</TableHead>
                  <TableHead>Frequency</TableHead>
                  <TableHead>Completeness</TableHead>
                  <TableHead>Quality</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredVariables.map((variable) => (
                  <TableRow 
                    key={variable.id} 
                    className="cursor-pointer hover:bg-blue-50 transition-colors"
                    onClick={() => setSelectedVariable(variable)}
                  >
                    <TableCell>
                      <div>
                        <div className="font-medium flex items-center space-x-2">
                          {getCategoryIcon(variable.category)}
                          <span>{variable.name}</span>
                          {variable.requiredField && <Badge variant="outline" className="text-xs">Required</Badge>}
                        </div>
                        <div className="text-sm text-muted-foreground mt-1">
                          {variable.description.length > 50 
                            ? `${variable.description.substring(0, 50)}...` 
                            : variable.description}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={getTemporalColor(variable.temporalCategory)} variant="secondary">
                        <div className="flex items-center space-x-1">
                          {getTemporalIcon(variable.temporalCategory)}
                          <span className="text-xs">{variable.temporalCategory}</span>
                        </div>
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{variable.measurementFrequency}</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-500 h-2 rounded-full" 
                            style={{ width: `${variable.completeness}%` }}
                          />
                        </div>
                        <span className="text-sm">{variable.completeness}%</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={getQualityColor(variable.quality)}>
                        {variable.quality}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Variable Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {selectedVariable ? "Variable Details" : "Select a Variable"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {selectedVariable ? (
              <div className="space-y-4">
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    {getCategoryIcon(selectedVariable.category)}
                    <h3 className="font-medium">{selectedVariable.name}</h3>
                  </div>
                  <p className="text-sm text-muted-foreground">{selectedVariable.description}</p>
                </div>

                <Tabs defaultValue="basic" className="space-y-3">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="basic" className="text-xs">Basic Info</TabsTrigger>
                    <TabsTrigger value="temporal" className="text-xs">Temporal</TabsTrigger>
                  </TabsList>

                  <TabsContent value="basic" className="space-y-3">
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label className="text-xs font-medium text-muted-foreground">Category</Label>
                          <p className="text-sm">{selectedVariable.category}</p>
                        </div>
                        <div>
                          <Label className="text-xs font-medium text-muted-foreground">Data Type</Label>
                          <p className="text-sm">{selectedVariable.dataType}</p>
                        </div>
                      </div>

                      {selectedVariable.units && (
                        <div>
                          <Label className="text-xs font-medium text-muted-foreground">Units</Label>
                          <p className="text-sm">{selectedVariable.units}</p>
                        </div>
                      )}

                      {selectedVariable.referenceRange && (
                        <div>
                          <Label className="text-xs font-medium text-muted-foreground">Reference Range</Label>
                          <p className="text-sm">{selectedVariable.referenceRange}</p>
                        </div>
                      )}

                      {selectedVariable.validValues && (
                        <div>
                          <Label className="text-xs font-medium text-muted-foreground">Valid Values</Label>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {selectedVariable.validValues.map((value) => (
                              <Badge key={value} variant="outline" className="text-xs">
                                {value}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label className="text-xs font-medium text-muted-foreground">Source</Label>
                          <p className="text-sm">{selectedVariable.source}</p>
                        </div>
                        <div>
                          <Label className="text-xs font-medium text-muted-foreground">Last Updated</Label>
                          <p className="text-sm">{selectedVariable.lastUpdated}</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label className="text-xs font-medium text-muted-foreground">Completeness</Label>
                          <div className="flex items-center space-x-2 mt-1">
                            <div className="w-16 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-blue-500 h-2 rounded-full" 
                                style={{ width: `${selectedVariable.completeness}%` }}
                              />
                            </div>
                            <span className="text-sm">{selectedVariable.completeness}%</span>
                          </div>
                        </div>
                        <div>
                          <Label className="text-xs font-medium text-muted-foreground">Quality</Label>
                          <Badge className={getQualityColor(selectedVariable.quality)} variant="secondary">
                            {selectedVariable.quality}
                          </Badge>
                        </div>
                      </div>

                      {selectedVariable.derivedFrom && (
                        <div>
                          <Label className="text-xs font-medium text-muted-foreground">Derived From</Label>
                          <div className="mt-1 space-y-1">
                            {selectedVariable.derivedFrom.map((dep) => (
                              <Badge key={dep} variant="outline" className="text-xs mr-1">
                                {dep.replace(/_/g, ' ')}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </TabsContent>

                  <TabsContent value="temporal" className="space-y-3">
                    <div className="space-y-3">
                      <div>
                        <Label className="text-xs font-medium text-muted-foreground">Temporal Category</Label>
                        <Badge className={getTemporalColor(selectedVariable.temporalCategory)} variant="secondary">
                          <div className="flex items-center space-x-1">
                            {getTemporalIcon(selectedVariable.temporalCategory)}
                            <span className="text-xs">{selectedVariable.temporalCategory}</span>
                          </div>
                        </Badge>
                      </div>

                      <div>
                        <Label className="text-xs font-medium text-muted-foreground">Measurement Frequency</Label>
                        <p className="text-sm">{selectedVariable.measurementFrequency}</p>
                      </div>

                      <div>
                        <Label className="text-xs font-medium text-muted-foreground">Valid Comparison Timeframe</Label>
                        <p className="text-sm bg-blue-50 p-2 rounded text-blue-700">{selectedVariable.validComparisonTimeframe}</p>
                      </div>

                      {selectedVariable.temporalConsiderations && (
                        <div>
                          <Label className="text-xs font-medium text-muted-foreground">Temporal Considerations</Label>
                          <p className="text-sm bg-yellow-50 p-2 rounded text-yellow-800">{selectedVariable.temporalConsiderations}</p>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                </Tabs>

                {/* Clinical Context */}
                {selectedVariable.clinicalSignificance && (
                  <div className="border-t pt-3">
                    <Label className="text-xs font-medium text-muted-foreground">Clinical Significance</Label>
                    <p className="text-sm mt-1">{selectedVariable.clinicalSignificance}</p>
                  </div>
                )}

                {/* Technical Details */}
                {(selectedVariable.methodology || selectedVariable.limitations) && (
                  <div className="border-t pt-3 space-y-3">
                    {selectedVariable.methodology && (
                      <div>
                        <Label className="text-xs font-medium text-muted-foreground">Methodology</Label>
                        <p className="text-sm mt-1 bg-gray-50 p-2 rounded">{selectedVariable.methodology}</p>
                      </div>
                    )}

                    {selectedVariable.limitations && (
                      <div>
                        <Label className="text-xs font-medium text-muted-foreground">Limitations</Label>
                        <p className="text-sm mt-1 bg-red-50 p-2 rounded text-red-700">{selectedVariable.limitations}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-8">
                <MousePointer className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Click any variable from the table to view detailed information</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>



      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Variables</p>
                <p className="text-2xl">{dataVariables.length}</p>
              </div>
              <Database className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Temporal Types</p>
                <p className="text-2xl">{temporalCategories.length - 1}</p>
              </div>
              <Clock className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">High Quality</p>
                <p className="text-2xl">{dataVariables.filter(v => v.quality === 'high').length}</p>
              </div>
              <Info className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Repeated Measures</p>
                <p className="text-2xl">{dataVariables.filter(v => v.temporalCategory === 'repeated-measures').length}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* FAIR Data Tools Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Shield className="h-5 w-5 text-primary" />
            <span>FAIR Data Tools & Compliance</span>
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Certify, annotate, and export registry datasets following FAIR principles (Findable, Accessible, Interoperable, Reusable)
          </p>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="certification" className="space-y-4">
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="certification">Certification</TabsTrigger>
              <TabsTrigger value="annotation">Annotation</TabsTrigger>
              <TabsTrigger value="validation">Validation</TabsTrigger>
              <TabsTrigger value="linkage">External Linkage</TabsTrigger>
              <TabsTrigger value="export">Export Metadata</TabsTrigger>
            </TabsList>

            <TabsContent value="certification" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">FAIR Principles Certification</CardTitle>
                  <p className="text-sm text-muted-foreground">Assess and certify dataset compliance with FAIR principles</p>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <Search className="h-4 w-4 text-blue-600" />
                          <span className="font-medium">Findable</span>
                        </div>
                        <Badge className="bg-green-100 text-green-800">95%</Badge>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Persistent identifiers</span>
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Rich metadata</span>
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Indexed in searchable resource</span>
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        </div>
                      </div>
                    </div>

                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <Database className="h-4 w-4 text-green-600" />
                          <span className="font-medium">Accessible</span>
                        </div>
                        <Badge className="bg-green-100 text-green-800">92%</Badge>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Open/standard protocol</span>
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Authentication/authorization</span>
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Metadata persistence</span>
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        </div>
                      </div>
                    </div>

                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <Link2 className="h-4 w-4 text-purple-600" />
                          <span className="font-medium">Interoperable</span>
                        </div>
                        <Badge className="bg-yellow-100 text-yellow-800">85%</Badge>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Formal language</span>
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">FAIR vocabularies</span>
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Qualified references</span>
                          <AlertCircle className="h-4 w-4 text-yellow-600" />
                        </div>
                      </div>
                    </div>

                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <FileText className="h-4 w-4 text-orange-600" />
                          <span className="font-medium">Reusable</span>
                        </div>
                        <Badge className="bg-green-100 text-green-800">90%</Badge>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Clear usage license</span>
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Provenance information</span>
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-muted-foreground">Community standards</span>
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="border-t pt-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Overall FAIR Compliance Score</p>
                        <p className="text-sm text-muted-foreground">Weighted average across all principles</p>
                      </div>
                      <div className="text-3xl text-primary">91%</div>
                    </div>
                    <div className="mt-4 flex space-x-2">
                      <Button>
                        <Download className="h-4 w-4 mr-2" />
                        Download Certificate
                      </Button>
                      <Button variant="outline">
                        <Info className="h-4 w-4 mr-2" />
                        View Guidelines
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="annotation" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Dataset Annotation & Metadata Enrichment</CardTitle>
                  <p className="text-sm text-muted-foreground">Add semantic annotations and controlled vocabularies</p>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium mb-3">Ontology Mappings</h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 bg-blue-50 rounded">
                        <div>
                          <p className="font-medium text-sm">SNOMED CT</p>
                          <p className="text-xs text-muted-foreground">Clinical terminology mappings</p>
                        </div>
                        <Badge className="bg-green-100 text-green-800">{patientCount} mapped</Badge>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-purple-50 rounded">
                        <div>
                          <p className="font-medium text-sm">LOINC</p>
                          <p className="text-xs text-muted-foreground">Laboratory observations</p>
                        </div>
                        <Badge className="bg-green-100 text-green-800">856 mapped</Badge>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-green-50 rounded">
                        <div>
                          <p className="font-medium text-sm">ICD-10</p>
                          <p className="text-xs text-muted-foreground">Diagnosis codes</p>
                        </div>
                        <Badge className="bg-green-100 text-green-800">342 mapped</Badge>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-orange-50 rounded">
                        <div>
                          <p className="font-medium text-sm">RxNorm</p>
                          <p className="text-xs text-muted-foreground">Medication coding</p>
                        </div>
                        <Badge className="bg-yellow-100 text-yellow-800">198 mapped</Badge>
                      </div>
                    </div>
                  </div>

                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium mb-3">Semantic Tags & Keywords</h4>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="outline">cardiovascular disease</Badge>
                      <Badge variant="outline">precision medicine</Badge>
                      <Badge variant="outline">genomics</Badge>
                      <Badge variant="outline">biomarkers</Badge>
                      <Badge variant="outline">longitudinal cohort</Badge>
                      <Badge variant="outline">risk stratification</Badge>
                      <Badge variant="outline">clinical outcomes</Badge>
                      <Button variant="outline" size="sm">+ Add Tag</Button>
                    </div>
                  </div>

                  <div className="flex space-x-2">
                    <Button>
                      <Save className="h-4 w-4 mr-2" />
                      Save Annotations
                    </Button>
                    <Button variant="outline">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Map to Ontology
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="validation" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Data Validation Wizard</CardTitle>
                  <p className="text-sm text-muted-foreground">Automated quality checks and validation rules</p>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium">Schema Validation</h4>
                        <Badge className="bg-green-100 text-green-800">Passed</Badge>
                      </div>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Required fields</span>
                          <span className="font-medium">98.5% complete</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Data types</span>
                          <span className="font-medium">100% valid</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Unique constraints</span>
                          <span className="font-medium">No violations</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Value ranges</span>
                          <span className="font-medium">99.2% valid</span>
                        </div>
                      </div>
                    </div>

                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium">Temporal Consistency</h4>
                        <Badge className="bg-green-100 text-green-800">Passed</Badge>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Date ordering</span>
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Event sequencing</span>
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Follow-up intervals</span>
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        </div>
                      </div>
                    </div>

                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium">Cross-field Validation</h4>
                        <Badge className="bg-yellow-100 text-yellow-800">3 Warnings</Badge>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex items-start space-x-2 text-yellow-700">
                          <AlertCircle className="h-4 w-4 mt-0.5" />
                          <span>12 patients with BMI calculation mismatch (height/weight inconsistency)</span>
                        </div>
                        <div className="flex items-start space-x-2 text-yellow-700">
                          <AlertCircle className="h-4 w-4 mt-0.5" />
                          <span>5 records with age/date of birth discrepancy</span>
                        </div>
                        <div className="flex items-start space-x-2 text-yellow-700">
                          <AlertCircle className="h-4 w-4 mt-0.5" />
                          <span>8 patients with medication dates outside enrollment period</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex space-x-2">
                    <Button>
                      <Play className="h-4 w-4 mr-2" />
                      Run Full Validation
                    </Button>
                    <Button variant="outline">
                      <Download className="h-4 w-4 mr-2" />
                      Export Report
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="linkage" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">External Database Linkage</CardTitle>
                  <p className="text-sm text-muted-foreground">Connect to research repositories and databases</p>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <ExternalLink className="h-4 w-4 text-blue-600" />
                          <h4 className="font-medium">ClinicalTrials.gov</h4>
                        </div>
                        <Badge className="bg-green-100 text-green-800">Connected</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">NIH clinical trials registry</p>
                      <Button variant="outline" size="sm" className="w-full">
                        <Link2 className="h-4 w-4 mr-2" />
                        View Linked Trials (12)
                      </Button>
                    </div>

                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <ExternalLink className="h-4 w-4 text-purple-600" />
                          <h4 className="font-medium">dbGaP</h4>
                        </div>
                        <Badge className="bg-green-100 text-green-800">Connected</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">Database of Genotypes and Phenotypes</p>
                      <Button variant="outline" size="sm" className="w-full">
                        <Link2 className="h-4 w-4 mr-2" />
                        View Studies (3)
                      </Button>
                    </div>

                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <ExternalLink className="h-4 w-4 text-green-600" />
                          <h4 className="font-medium">PubMed</h4>
                        </div>
                        <Badge className="bg-green-100 text-green-800">Connected</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">Biomedical literature database</p>
                      <Button variant="outline" size="sm" className="w-full">
                        <Link2 className="h-4 w-4 mr-2" />
                        View Publications (48)
                      </Button>
                    </div>

                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <ExternalLink className="h-4 w-4 text-orange-600" />
                          <h4 className="font-medium">OMIM</h4>
                        </div>
                        <Badge variant="outline">Not Connected</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">Online Mendelian Inheritance in Man</p>
                      <Button variant="outline" size="sm" className="w-full">
                        <Link2 className="h-4 w-4 mr-2" />
                        Connect Database
                      </Button>
                    </div>

                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <ExternalLink className="h-4 w-4 text-red-600" />
                          <h4 className="font-medium">ClinVar</h4>
                        </div>
                        <Badge variant="outline">Not Connected</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">Genomic variation database</p>
                      <Button variant="outline" size="sm" className="w-full">
                        <Link2 className="h-4 w-4 mr-2" />
                        Connect Database
                      </Button>
                    </div>

                    <div className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <ExternalLink className="h-4 w-4 text-indigo-600" />
                          <h4 className="font-medium">Zenodo</h4>
                        </div>
                        <Badge className="bg-green-100 text-green-800">Connected</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">Research data repository</p>
                      <Button variant="outline" size="sm" className="w-full">
                        <Link2 className="h-4 w-4 mr-2" />
                        View Datasets (7)
                      </Button>
                    </div>
                  </div>

                  <Button className="w-full">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Add New Database Connection
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="export" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Machine-Readable Metadata Export</CardTitle>
                  <p className="text-sm text-muted-foreground">Generate standardized metadata in multiple formats</p>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="border rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-3">
                        <FileJson className="h-5 w-5 text-blue-600" />
                        <h4 className="font-medium">JSON-LD</h4>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">
                        Linked Data format with schema.org vocabulary
                      </p>
                      <div className="space-y-2">
                        <Button variant="outline" size="sm" className="w-full">
                          <Download className="h-4 w-4 mr-2" />
                          Download JSON-LD
                        </Button>
                        <Button variant="ghost" size="sm" className="w-full">
                          <Info className="h-4 w-4 mr-2" />
                          View Preview
                        </Button>
                      </div>
                    </div>

                    <div className="border rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-3">
                        <FileText className="h-5 w-5 text-green-600" />
                        <h4 className="font-medium">DataCite XML</h4>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">
                        DOI registration and citation metadata
                      </p>
                      <div className="space-y-2">
                        <Button variant="outline" size="sm" className="w-full">
                          <Download className="h-4 w-4 mr-2" />
                          Download DataCite XML
                        </Button>
                        <Button variant="ghost" size="sm" className="w-full">
                          <Info className="h-4 w-4 mr-2" />
                          View Preview
                        </Button>
                      </div>
                    </div>

                    <div className="border rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-3">
                        <Database className="h-5 w-5 text-purple-600" />
                        <h4 className="font-medium">DCAT-AP</h4>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">
                        Data Catalog Vocabulary for European standards
                      </p>
                      <div className="space-y-2">
                        <Button variant="outline" size="sm" className="w-full">
                          <Download className="h-4 w-4 mr-2" />
                          Download DCAT-AP
                        </Button>
                        <Button variant="ghost" size="sm" className="w-full">
                          <Info className="h-4 w-4 mr-2" />
                          View Preview
                        </Button>
                      </div>
                    </div>

                    <div className="border rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-3">
                        <FileText className="h-5 w-5 text-orange-600" />
                        <h4 className="font-medium">FHIR</h4>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">
                        Fast Healthcare Interoperability Resources
                      </p>
                      <div className="space-y-2">
                        <Button variant="outline" size="sm" className="w-full">
                          <Download className="h-4 w-4 mr-2" />
                          Download FHIR Bundle
                        </Button>
                        <Button variant="ghost" size="sm" className="w-full">
                          <Info className="h-4 w-4 mr-2" />
                          View Preview
                        </Button>
                      </div>
                    </div>
                  </div>

                  <div className="border rounded-lg p-4">
                    <h4 className="font-medium mb-3">Export Summary</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Variables</p>
                        <p className="font-medium">{dataVariables.length}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Patients</p>
                        <p className="font-medium">3,847</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Observations</p>
                        <p className="font-medium">124,589</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">Data Volume</p>
                        <p className="font-medium">2.4 GB</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex space-x-2">
                    <Button className="flex-1">
                      <Download className="h-4 w-4 mr-2" />
                      Export All Formats
                    </Button>
                    <Button variant="outline">
                      <FileJson className="h-4 w-4 mr-2" />
                      Custom Export
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

    </div>
  );
}