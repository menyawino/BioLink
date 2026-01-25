/**
 * Tool Definitions for BioLink Agent
 * Complete coverage of all platform functionalities
 */

export interface ToolParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  description: string;
  required: boolean;
  enum?: string[];
  items?: { type: string };
  properties?: Record<string, ToolParameter>;
}

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: ToolParameter[];
  category: 'patient' | 'cohort' | 'analytics' | 'chart' | 'navigation' | 'data' | 'export';
}

export const AGENT_TOOLS: ToolDefinition[] = [
  // === PATIENT MANAGEMENT TOOLS ===
  {
    name: 'search_patients',
    description: 'Search and filter patients in the registry. Returns patient list with demographics and data completeness.',
    category: 'patient',
    parameters: [
      { name: 'search', type: 'string', description: 'Search by DNA ID, nationality, or city', required: false },
      { name: 'gender', type: 'string', description: 'Filter by gender', required: false, enum: ['Male', 'Female'] },
      { name: 'ageMin', type: 'number', description: 'Minimum age filter', required: false },
      { name: 'ageMax', type: 'number', description: 'Maximum age filter', required: false },
      { name: 'limit', type: 'number', description: 'Number of results to return (max 500)', required: false },
      { name: 'sortBy', type: 'string', description: 'Field to sort by', required: false, enum: ['dna_id', 'age', 'enrollment_date', 'data_completeness'] },
      { name: 'sortOrder', type: 'string', description: 'Sort direction', required: false, enum: ['asc', 'desc'] }
    ]
  },
  {
    name: 'get_patient_details',
    description: 'Get complete details for a specific patient including all clinical data, imaging, labs, and history.',
    category: 'patient',
    parameters: [
      { name: 'dnaId', type: 'string', description: 'Patient DNA ID (e.g., EHV001)', required: true }
    ]
  },
  {
    name: 'get_patient_vitals',
    description: 'Get vital signs and physical examination data for a patient.',
    category: 'patient',
    parameters: [
      { name: 'dnaId', type: 'string', description: 'Patient DNA ID', required: true }
    ]
  },
  {
    name: 'get_patient_imaging',
    description: 'Get echocardiography and MRI imaging data for a patient.',
    category: 'patient',
    parameters: [
      { name: 'dnaId', type: 'string', description: 'Patient DNA ID', required: true }
    ]
  },
  {
    name: 'get_patient_risk_factors',
    description: 'Get cardiovascular risk factors and ASCVD risk score for a patient.',
    category: 'patient',
    parameters: [
      { name: 'dnaId', type: 'string', description: 'Patient DNA ID', required: true }
    ]
  },

  // === COHORT BUILDER TOOLS ===
  {
    name: 'build_cohort',
    description: 'Build a patient cohort with comprehensive filtering criteria including demographics, clinical, temporal, data availability, and geographic filters.',
    category: 'cohort',
    parameters: [
      { name: 'ageMin', type: 'number', description: 'Minimum age (default 18)', required: false },
      { name: 'ageMax', type: 'number', description: 'Maximum age (default 90)', required: false },
      { name: 'gender', type: 'string', description: 'Gender filter', required: false, enum: ['Male', 'Female'] },
      { name: 'nationality', type: 'string', description: 'Filter by nationality', required: false },
      { name: 'hasDiabetes', type: 'boolean', description: 'Filter patients with diabetes', required: false },
      { name: 'hasHypertension', type: 'boolean', description: 'Filter patients with hypertension', required: false },
      { name: 'hasSmoking', type: 'boolean', description: 'Filter current smokers', required: false },
      { name: 'hasObesity', type: 'boolean', description: 'Filter patients with BMI >= 30', required: false },
      { name: 'hasFamilyHistory', type: 'boolean', description: 'Filter patients with family history of CVD', required: false },
      { name: 'hasEcho', type: 'boolean', description: 'Require echocardiography data', required: false },
      { name: 'hasMri', type: 'boolean', description: 'Require MRI data', required: false },
      { name: 'hasLabs', type: 'boolean', description: 'Require laboratory data', required: false },
      { name: 'hasImaging', type: 'boolean', description: 'Require any imaging data', required: false },
      { name: 'minDataCompleteness', type: 'number', description: 'Minimum data completeness percentage (0-100)', required: false },
      { name: 'enrollmentDateFrom', type: 'string', description: 'Enrollment start date (YYYY-MM-DD)', required: false },
      { name: 'enrollmentDateTo', type: 'string', description: 'Enrollment end date (YYYY-MM-DD)', required: false },
      { name: 'region', type: 'string', description: 'Geographic region filter', required: false },
      { name: 'limit', type: 'number', description: 'Maximum results (default 500)', required: false }
    ]
  },
  {
    name: 'estimate_cohort_size',
    description: 'Get estimated patient count for cohort criteria without executing full query.',
    category: 'cohort',
    parameters: [
      { name: 'ageMin', type: 'number', description: 'Minimum age', required: false },
      { name: 'ageMax', type: 'number', description: 'Maximum age', required: false },
      { name: 'gender', type: 'string', description: 'Gender filter', required: false },
      { name: 'hasDiabetes', type: 'boolean', description: 'Has diabetes', required: false },
      { name: 'hasHypertension', type: 'boolean', description: 'Has hypertension', required: false }
    ]
  },
  {
    name: 'export_cohort',
    description: 'Export cohort results to CSV or JSON format with full patient data and metadata.',
    category: 'export',
    parameters: [
      { name: 'cohortId', type: 'string', description: 'Cohort query identifier', required: true },
      { name: 'format', type: 'string', description: 'Export format', required: true, enum: ['csv', 'json'] },
      { name: 'includeFields', type: 'array', description: 'Specific fields to include', required: false, items: { type: 'string' } }
    ]
  },

  // === ANALYTICS TOOLS ===
  {
    name: 'get_registry_overview',
    description: 'Get high-level registry statistics including total patients, gender distribution, average age, and data completeness.',
    category: 'analytics',
    parameters: []
  },
  {
    name: 'get_demographics_analysis',
    description: 'Analyze patient demographics including age/gender distribution, nationality breakdown, and marital status.',
    category: 'analytics',
    parameters: []
  },
  {
    name: 'get_clinical_metrics',
    description: 'Get clinical metric distributions including BMI, blood pressure, ejection fraction, and HbA1c.',
    category: 'analytics',
    parameters: []
  },
  {
    name: 'get_comorbidity_analysis',
    description: 'Analyze comorbidity patterns and prevalence across the registry.',
    category: 'analytics',
    parameters: []
  },
  {
    name: 'get_lifestyle_statistics',
    description: 'Get lifestyle data statistics including smoking rates, alcohol consumption, and medication use.',
    category: 'analytics',
    parameters: []
  },
  {
    name: 'get_geographic_distribution',
    description: 'Analyze geographic distribution of patients by city and region.',
    category: 'analytics',
    parameters: []
  },
  {
    name: 'get_enrollment_trends',
    description: 'Get patient enrollment trends over time.',
    category: 'analytics',
    parameters: []
  },
  {
    name: 'get_data_quality_metrics',
    description: 'Analyze data completeness and quality across all categories.',
    category: 'analytics',
    parameters: []
  },
  {
    name: 'get_imaging_statistics',
    description: 'Get statistics for echocardiography and MRI data including coverage and measurement distributions.',
    category: 'analytics',
    parameters: []
  },
  {
    name: 'get_ecg_analysis',
    description: 'Analyze ECG data including rhythm distribution, abnormalities, and conclusions.',
    category: 'analytics',
    parameters: []
  },

  // === CHART BUILDER TOOLS ===
  {
    name: 'create_chart',
    description: 'Create a custom data visualization chart with specified type, axes, and grouping.',
    category: 'chart',
    parameters: [
      { name: 'chartType', type: 'string', description: 'Type of chart', required: true, enum: ['bar', 'line', 'scatter', 'pie'] },
      { name: 'xAxis', type: 'string', description: 'X-axis field', required: true },
      { name: 'yAxis', type: 'string', description: 'Y-axis field (not required for pie charts)', required: false },
      { name: 'groupBy', type: 'string', description: 'Field to group/categorize by', required: false },
      { name: 'aggregation', type: 'string', description: 'Aggregation method', required: false, enum: ['count', 'avg', 'sum', 'min', 'max'] }
    ]
  },
  {
    name: 'get_available_chart_fields',
    description: 'Get list of all fields available for charting with their data types and descriptions.',
    category: 'chart',
    parameters: []
  },
  {
    name: 'get_chart_data',
    description: 'Get aggregated data for a specific chart configuration.',
    category: 'chart',
    parameters: [
      { name: 'xAxis', type: 'string', description: 'X-axis field', required: true },
      { name: 'yAxis', type: 'string', description: 'Y-axis field', required: false },
      { name: 'groupBy', type: 'string', description: 'Grouping field', required: false },
      { name: 'filters', type: 'object', description: 'Additional filters', required: false, properties: {} }
    ]
  },

  // === DATA DICTIONARY TOOLS ===
  {
    name: 'search_data_dictionary',
    description: 'Search for field definitions, descriptions, and metadata in the data dictionary.',
    category: 'data',
    parameters: [
      { name: 'query', type: 'string', description: 'Search term for field names or descriptions', required: true },
      { name: 'category', type: 'string', description: 'Filter by category', required: false, enum: ['Demographics', 'Clinical', 'Imaging', 'Labs', 'Lifestyle', 'Geographic', 'Family History'] }
    ]
  },
  {
    name: 'get_field_metadata',
    description: 'Get detailed metadata for a specific database field including type, description, statistics, and completeness.',
    category: 'data',
    parameters: [
      { name: 'fieldName', type: 'string', description: 'Database field name', required: true }
    ]
  },
  {
    name: 'get_category_fields',
    description: 'List all fields in a specific data category.',
    category: 'data',
    parameters: [
      { name: 'category', type: 'string', description: 'Data category', required: true, enum: ['Demographics', 'Clinical', 'Imaging', 'Labs', 'Lifestyle', 'Geographic', 'Family History', 'Physical Exam', 'ECG', 'Medical History'] }
    ]
  },

  // === NAVIGATION TOOLS ===
  {
    name: 'navigate_to_view',
    description: 'Navigate to a different section/view of the platform.',
    category: 'navigation',
    parameters: [
      { name: 'view', type: 'string', description: 'Target view', required: true, enum: ['welcome', 'patient', 'registry', 'cohort', 'analytics', 'charts', 'dictionary', 'settings', 'profile'] }
    ]
  },
  {
    name: 'open_patient_profile',
    description: 'Navigate to and open a specific patient\'s detailed profile.',
    category: 'navigation',
    parameters: [
      { name: 'dnaId', type: 'string', description: 'Patient DNA ID', required: true }
    ]
  },
  {
    name: 'get_current_view',
    description: 'Get information about the current view/section the user is in.',
    category: 'navigation',
    parameters: []
  },

  // === EXPORT TOOLS ===
  {
    name: 'export_patients',
    description: 'Export patient data to CSV format.',
    category: 'export',
    parameters: [
      { name: 'patientIds', type: 'array', description: 'Array of DNA IDs to export', required: true, items: { type: 'string' } },
      { name: 'includeFields', type: 'array', description: 'Fields to include in export', required: false, items: { type: 'string' } }
    ]
  },
  {
    name: 'export_analytics',
    description: 'Export analytics data and visualizations.',
    category: 'export',
    parameters: [
      { name: 'analysisType', type: 'string', description: 'Type of analysis to export', required: true, enum: ['demographics', 'clinical', 'geographic', 'trends'] },
      { name: 'format', type: 'string', description: 'Export format', required: true, enum: ['csv', 'json', 'pdf'] }
    ]
  },
  {
    name: 'export_chart',
    description: 'Export chart visualization as image or data.',
    category: 'export',
    parameters: [
      { name: 'chartId', type: 'string', description: 'Chart identifier', required: true },
      { name: 'format', type: 'string', description: 'Export format', required: true, enum: ['png', 'svg', 'csv', 'json'] }
    ]
  }
];

// Tool execution result type
export interface ToolExecutionResult {
  success: boolean;
  data?: any;
  error?: string;
  message?: string;
  requiresUserConfirmation?: boolean;
  nextSteps?: string[];
}

// Tool call interface
export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string; // JSON string
  };
}
