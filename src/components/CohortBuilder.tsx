import { useState, useMemo, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Checkbox } from "./ui/checkbox";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Slider } from "./ui/slider";
import { Textarea } from "./ui/textarea";
import { Save, Download, Play, Users, Filter, Database, Map, Clock, BookOpen, Beaker, CheckCircle2, AlertCircle, UserCheck, ClipboardList, TrendingUp, FileText, Loader2 } from "lucide-react";
import { useCohortQuery, useCohortEstimate, useDownloadCohort } from "../hooks/useCohort";
import { useCohortFilterOptions, useRegistryOverview } from "../hooks/useAnalytics";
import type { CohortFilterOption, Patient } from "../api/types";
import type { DatasetFilter, PatientsQueryParams } from "../api/patients";
import { useApp } from "../context/AppContext";

const DATASET_OPTIONS: Array<{ value: DatasetFilter; label: string }> = [
  { value: "all", label: "All registries" },
  { value: "ehvol", label: "EHVol" },
  { value: "bhs", label: "BHS" },
];

const DEFAULT_AGE_RANGE: [number, number] = [0, 100];
const SAVED_COHORTS_STORAGE_KEY = "biolink_saved_cohorts";

interface SavedCohort {
  id: number;
  name: string;
  size: number;
  lastModified: string;
  description: string;
  dataset: DatasetFilter;
  criteria: CohortCriteria;
}

interface CohortCriteria {
  demographics: {
    ageRange: [number, number];
    gender: string[];
    nationality: string[];
  };
  clinical: {
    diagnoses: string[];
    riskFactors: string[];
  };
  temporal: {
    enrollmentPeriod: [string, string];
  };
  dataAvailability: {
    requiredData: string[];
    minimumCompleteness: number;
  };
  geographic: {
    regions: string[];
  };
}

export function CohortBuilder() {
  const { setCurrentView, setCohortCriteria, setCohortResults } = useApp();
  const [cohortName, setCohortName] = useState("");
  const [description, setDescription] = useState("");
  const [queryExecuted, setQueryExecuted] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<DatasetFilter>("all");
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [criteria, setCriteria] = useState<CohortCriteria>({
    demographics: {
      ageRange: DEFAULT_AGE_RANGE,
      gender: [],
      nationality: []
    },
    clinical: {
      diagnoses: [],
      riskFactors: []
    },
    temporal: {
      enrollmentPeriod: ["", ""]
    },
    dataAvailability: {
      requiredData: [],
      minimumCompleteness: 0
    },
    geographic: {
      regions: []
    }
  });

  // Build query params from all criteria (memoized for performance)
  const estimateParams = useMemo((): PatientsQueryParams => {
    const params: PatientsQueryParams = {
      dataset: selectedDataset,
      gender: criteria.demographics.gender.length > 0 ? criteria.demographics.gender[0] : undefined,
      
      // Temporal filters
      enrollmentDateFrom: criteria.temporal.enrollmentPeriod[0] || undefined,
      enrollmentDateTo: criteria.temporal.enrollmentPeriod[1] || undefined,

      // Geographic filters
      region: criteria.geographic.regions.length > 0 ? criteria.geographic.regions[0] : undefined,
    };

    const [ageMin, ageMax] = criteria.demographics.ageRange;
    if (ageMin !== DEFAULT_AGE_RANGE[0] || ageMax !== DEFAULT_AGE_RANGE[1]) {
      params.ageMin = ageMin;
      params.ageMax = ageMax;
    }

    if (criteria.dataAvailability.minimumCompleteness > 0) {
      params.minDataCompleteness = criteria.dataAvailability.minimumCompleteness;
    }
    
    // Map data availability requirements
    const requiredData = criteria.dataAvailability.requiredData;
    if (requiredData.includes('Imaging')) params.hasImaging = true;
    if (requiredData.includes('Genomics')) params.hasGenomics = true;
    if (requiredData.includes('Clinical Labs') || requiredData.includes('Biomarkers')) params.hasLabs = true;
    
    // Map risk factors to clinical filters
    const riskFactors = criteria.clinical.riskFactors;
    if (riskFactors.includes('Diabetes')) params.hasDiabetes = true;
    if (riskFactors.includes('High Blood Pressure')) params.hasHypertension = true;
    if (riskFactors.includes('Smoking')) params.hasSmoking = true;
    if (riskFactors.includes('Obesity')) params.hasObesity = true;
    if (riskFactors.includes('Family History')) params.hasFamilyHistory = true;
    
    // Map diagnoses
    if (criteria.clinical.diagnoses.includes('Hypertension')) params.hasHypertension = true;
    if (criteria.clinical.diagnoses.includes('Diabetes Mellitus')) params.hasDiabetes = true;
    if (criteria.clinical.diagnoses.includes('Dyslipidemia')) params.hasDyslipidemia = true;
    if (criteria.clinical.diagnoses.includes('Coronary Heart Disease / Angina')) params.hasCoronaryDisease = true;
    if (criteria.clinical.diagnoses.includes('Heart Failure')) params.hasHeartFailure = true;
    
    // Nationality
    if (criteria.demographics.nationality.length > 0) params.nationality = criteria.demographics.nationality[0];

    if (requiredData.includes('Echocardiography')) params.hasEcho = true;
    if (requiredData.includes('Cardiac MRI')) params.hasMri = true;
    if (riskFactors.includes('Dyslipidemia')) params.hasDyslipidemia = true;
    
    return params;
  }, [criteria, selectedDataset]);

  // Use hooks for API integration
  const { mutate: executeQuery, isLoading: queryLoading, data: queryData } = useCohortQuery();
  const { data: estimateData, isLoading: estimateLoading } = useCohortEstimate(estimateParams);
  const { mutate: downloadCohort } = useDownloadCohort();
  const {
    data: filterOptions,
    isLoading: filterOptionsLoading,
    error: filterOptionsError,
  } = useCohortFilterOptions(selectedDataset);
  
  // Get total patient count from registry overview
  const { data: overview } = useRegistryOverview(selectedDataset);
  const totalPatients = overview?.totalPatients ?? 0;

  const estimatedSize = estimateData?.count || 0;
  
  // Use patients from hook or empty array
  const patients = queryData || [];
  
  const [savedCohorts, setSavedCohorts] = useState<SavedCohort[]>([
    { id: 1, name: "CAD High Risk", size: 389, lastModified: "2024-12-15" },
    { id: 2, name: "Heart Failure Cohort", size: 156, lastModified: "2024-12-10" },
    { id: 3, name: "Genomics Complete", size: 1108, lastModified: "2024-12-08" }
  ].map((cohort) => ({
    ...cohort,
    description: "",
    dataset: "all" as DatasetFilter,
    criteria: {
      demographics: { ageRange: DEFAULT_AGE_RANGE, gender: [], nationality: [] },
      clinical: { diagnoses: [], riskFactors: [] },
      temporal: { enrollmentPeriod: ["", ""] },
      dataAvailability: { requiredData: [], minimumCompleteness: 0 },
      geographic: { regions: [] },
    },
  })));

  const isAgeFilteringAvailable = overview?.hasAgeData ?? false;

  const availableGenders = (filterOptions?.genders ?? []).filter((option) => option.count > 0);
  const availableNationalities = (filterOptions?.nationalities ?? []).filter(
    (option) => option.count > 0 && option.label !== "Unknown" && option.count < totalPatients
  );
  const availableDiagnoses = (filterOptions?.diagnoses ?? []).filter(
    (option) => option.count > 0 && option.count < totalPatients
  );
  const availableRiskFactors = (filterOptions?.riskFactors ?? []).filter(
    (option) => option.count > 0 && option.count < totalPatients
  );
  const availableDataTypes = (filterOptions?.dataTypes ?? []).filter(
    (option) => option.count > 0 && option.count < totalPatients
  );
  const availableRegions = (filterOptions?.regions ?? []).filter(
    (option) => option.count > 0 && option.label !== "Unknown" && option.count < totalPatients
  );

  useEffect(() => {
    if (!filterOptions) {
      return;
    }

    const allowedGenders = new Set(availableGenders.map((option) => option.label));
    const allowedNationalities = new Set(availableNationalities.map((option) => option.label));
    const allowedDiagnoses = new Set(availableDiagnoses.map((option) => option.label));
    const allowedRiskFactors = new Set(availableRiskFactors.map((option) => option.label));
    const allowedDataTypes = new Set(availableDataTypes.map((option) => option.label));
    const allowedRegions = new Set(availableRegions.map((option) => option.label));

    setCriteria((prev) => ({
      ...prev,
      demographics: {
        ...prev.demographics,
        gender: prev.demographics.gender.filter((value) => allowedGenders.has(value)),
        nationality: prev.demographics.nationality.filter((value) => allowedNationalities.has(value)),
      },
      clinical: {
        ...prev.clinical,
        diagnoses: prev.clinical.diagnoses.filter((value) => allowedDiagnoses.has(value)),
        riskFactors: prev.clinical.riskFactors.filter((value) => allowedRiskFactors.has(value)),
      },
      dataAvailability: {
        ...prev.dataAvailability,
        requiredData: prev.dataAvailability.requiredData.filter((value) => allowedDataTypes.has(value)),
      },
      geographic: {
        ...prev.geographic,
        regions: prev.geographic.regions.filter((value) => allowedRegions.has(value)),
      },
    }));
  }, [filterOptions, availableDataTypes, availableDiagnoses, availableGenders, availableNationalities, availableRegions, availableRiskFactors]);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(SAVED_COHORTS_STORAGE_KEY);
      if (!stored) {
        return;
      }

      const parsed = JSON.parse(stored) as SavedCohort[];
      if (Array.isArray(parsed) && parsed.length > 0) {
        setSavedCohorts(parsed);
      }
    } catch {
      // Ignore malformed saved cohorts and keep seeded defaults.
    }
  }, []);

  useEffect(() => {
    setCohortCriteria({
      dataset: selectedDataset,
      criteria,
      estimatedSize,
    });
  }, [criteria, estimatedSize, selectedDataset, setCohortCriteria]);

  useEffect(() => {
    setCohortResults(patients);
  }, [patients, setCohortResults]);

  useEffect(() => {
    if (isAgeFilteringAvailable) {
      return;
    }

    const [ageMin, ageMax] = criteria.demographics.ageRange;
    if (ageMin === DEFAULT_AGE_RANGE[0] && ageMax === DEFAULT_AGE_RANGE[1]) {
      return;
    }

    setCriteria((prev) => ({
      ...prev,
      demographics: {
        ...prev.demographics,
        ageRange: DEFAULT_AGE_RANGE,
      },
    }));
    setActionMessage("Age filtering is unavailable for this dataset because the registry snapshot has no usable age values.");
  }, [criteria.demographics.ageRange, isAgeFilteringAvailable]);

  const updateCriteria = (section: keyof CohortCriteria, field: string, value: any) => {
    setCriteria(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  const addToArray = (section: keyof CohortCriteria, field: string, value: string) => {
    const currentArray = (criteria[section] as any)[field] as string[];
    if (!currentArray.includes(value)) {
      updateCriteria(section, field, [...currentArray, value]);
    }
  };

  const removeFromArray = (section: keyof CohortCriteria, field: string, value: string) => {
    const currentArray = (criteria[section] as any)[field] as string[];
    updateCriteria(section, field, currentArray.filter(item => item !== value));
  };

  const formatOptionLabel = (option: CohortFilterOption) => `${option.label} (${option.count.toLocaleString()})`;

  const handleDatasetChange = (value: string) => {
    setSelectedDataset(value as DatasetFilter);
    setQueryExecuted(false);
    setActionMessage(null);
  };

  const handleExecuteQuery = async () => {
    const params = { ...estimateParams, limit: 500 };
    if (!isAgeFilteringAvailable) {
      delete params.ageMin;
      delete params.ageMax;
    }

    await executeQuery(params);
    setQueryExecuted(true);
    setActionMessage(null);
  };

  const handleExportCriteria = () => {
    const exportContent = JSON.stringify(
      {
        cohortName: cohortName || "Unnamed Cohort",
        description,
        dataset: selectedDataset,
        criteria,
        estimatedSize,
      },
      null,
      2,
    );

    const blob = new Blob([exportContent], { type: "application/json" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cohort_criteria_${cohortName || "query"}_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    window.URL.revokeObjectURL(url);
    setActionMessage("Cohort criteria exported.");
  };

  const handleSaveCohort = () => {
    const savedCohort: SavedCohort = {
      id: Date.now(),
      name: cohortName.trim() || `Cohort ${new Date().toLocaleDateString()}`,
      size: estimatedSize,
      lastModified: new Date().toISOString().split("T")[0],
      description,
      dataset: selectedDataset,
      criteria,
    };

    const nextSavedCohorts = [savedCohort, ...savedCohorts.filter((cohort) => cohort.name !== savedCohort.name)].slice(0, 8);
    setSavedCohorts(nextSavedCohorts);
    window.localStorage.setItem(SAVED_COHORTS_STORAGE_KEY, JSON.stringify(nextSavedCohorts));
    setActionMessage(`Saved ${savedCohort.name}.`);
  };

  const handleLoadCohort = (cohort: SavedCohort) => {
    setCohortName(cohort.name);
    setDescription(cohort.description);
    setSelectedDataset(cohort.dataset);
    setCriteria(cohort.criteria);
    setQueryExecuted(false);
    setActionMessage(`Loaded ${cohort.name}.`);
  };

  const handleViewOnMap = () => {
    setCurrentView("analytics");
  };

  const handleDownloadCSV = () => {
    const headers = ["DNA ID", "Age", "Gender", "Nationality", "Enrollment Date", "Data Completeness", "Echo EF", "MRI EF"];
    const csvContent = [
      headers.join(","),
      ...patients.map(patient => 
        [
          patient.dna_id,
          patient.age ?? '',
          patient.gender ?? '',
          `"${patient.nationality || ''}"`,
          patient.enrollment_date ?? '',
          patient.data_completeness,
          patient.echo_ef ?? '',
          patient.mri_ef ?? ''
        ].join(",")
      )
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cohort_${cohortName || "query"}_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleDownloadJSON = () => {
    const jsonContent = JSON.stringify({
      cohortName: cohortName || "Unnamed Cohort",
      description: description,
      dataset: selectedDataset,
      executedDate: new Date().toISOString(),
      criteria: criteria,
      totalPatients: patients.length,
      patients: patients
    }, null, 2);

    const blob = new Blob([jsonContent], { type: "application/json" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cohort_${cohortName || "query"}_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const averageCompleteness = patients.length > 0
    ? Math.round(patients.reduce((sum, patient) => sum + patient.data_completeness, 0) / patients.length)
    : 0;

  const averageAge = patients.length > 0
    ? Math.round(patients.reduce((sum, patient) => sum + (patient.age || 0), 0) / patients.length)
    : 0;

  return (
    <div className="cohort-shell space-y-6">
      <div className="cohort-hero flex flex-wrap items-end justify-between gap-4">
        <div className="space-y-2">
          <span className="section-kicker">Cohort Workspace</span>
          <div>
            <h2 className="section-title">Advanced Cohort Builder</h2>
            <p className="section-subtitle max-w-3xl">
              Shape cohorts with filters that are actually queryable in the current registry snapshot.
            </p>
          </div>
        </div>

        <div className="registry-meta-grid grid gap-3 sm:grid-cols-3">
          <div className="metric-tile">
            <span className="metric-label">Estimated cohort</span>
            <strong className="metric-value">{estimateLoading ? '...' : estimatedSize.toLocaleString()}</strong>
          </div>
          <div className="metric-tile">
            <span className="metric-label">Registry population</span>
            <strong className="metric-value">{totalPatients.toLocaleString()}</strong>
          </div>
          <div className="metric-tile">
            <span className="metric-label">Min completeness</span>
            <strong className="metric-value">{criteria.dataAvailability.minimumCompleteness > 0 ? `${criteria.dataAvailability.minimumCompleteness}%` : 'Off'}</strong>
          </div>
        </div>
      </div>

      <Card className="cohort-builder-card">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="h-5 w-5" />
            <span>Advanced Cohort Builder</span>
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Build sophisticated patient cohorts with multi-dimensional filtering and temporal constraints
          </p>
            {filterOptionsLoading ? (
              <p className="text-xs text-muted-foreground">Loading live filter options from the registry...</p>
            ) : null}
            {filterOptionsError ? (
              <p className="text-xs text-destructive">Live filter options are unavailable right now. Query execution is still available.</p>
            ) : null}
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>Cohort Name</Label>
              <Input
                value={cohortName}
                onChange={(e) => setCohortName(e.target.value)}
                placeholder="Enter cohort name"
              />
            </div>
            <div>
              <Label>Dataset</Label>
              <Select value={selectedDataset} onValueChange={handleDatasetChange}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose registry dataset" />
                </SelectTrigger>
                <SelectContent>
                  {DATASET_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="mt-1 text-xs text-muted-foreground">
                Live filters, estimates, and counts update for the selected registry.
              </p>
            </div>
            <div className="flex items-end">
              <div className="text-center">
                <Label className="text-sm text-muted-foreground">Estimated Size</Label>
                {estimateLoading ? (
                  <div className="mt-2 space-y-2">
                    <div className="skeleton-block mx-auto h-8 w-24 rounded-2xl" />
                    <div className="skeleton-block mx-auto h-3 w-14 rounded-full" />
                  </div>
                ) : (
                  <div className="text-2xl">{estimatedSize.toLocaleString()}</div>
                )}
                <p className="text-xs text-muted-foreground">patients</p>
              </div>
            </div>
          </div>
          
          <div>
            <Label>Description</Label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the purpose and characteristics of this cohort"
              rows={2}
            />
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="demographics" className="space-y-4 cohort-tabs">
        <TabsList className="view-tabs-list view-tabs-scroll cohort-tabs-list w-full justify-start">
          <TabsTrigger value="demographics">Demographics</TabsTrigger>
          <TabsTrigger value="clinical">Clinical</TabsTrigger>
          <TabsTrigger value="temporal">Temporal</TabsTrigger>
          <TabsTrigger value="data">Data Requirements</TabsTrigger>
          <TabsTrigger value="geographic">Geographic</TabsTrigger>
          <TabsTrigger value="results" disabled={!queryExecuted}>
            Query Results {queryExecuted && `(${patients.length})`}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="demographics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Demographic Criteria</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>
                  Age Range: {criteria.demographics.ageRange[0] === DEFAULT_AGE_RANGE[0] && criteria.demographics.ageRange[1] === DEFAULT_AGE_RANGE[1]
                    ? 'Off'
                    : `${criteria.demographics.ageRange[0]} - ${criteria.demographics.ageRange[1]} years`}
                </Label>
                <Slider
                  value={criteria.demographics.ageRange}
                  onValueChange={(value: number[]) => updateCriteria('demographics', 'ageRange', value)}
                  max={100}
                  min={0}
                  step={1}
                  className="mt-2"
                  disabled={!isAgeFilteringAvailable}
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  {isAgeFilteringAvailable
                    ? 'Leave this at the full range unless you explicitly want to exclude patients by age.'
                    : 'Disabled because this dataset does not currently contain usable age values.'}
                </p>
              </div>

              <div>
                <Label>Gender</Label>
                <div className="flex space-x-2 mt-2">
                  {availableGenders.length > 0 ? availableGenders.map((gender) => (
                    <div key={gender.label} className="flex items-center space-x-2">
                      <Checkbox
                        checked={criteria.demographics.gender.includes(gender.label)}
                        onCheckedChange={(checked: boolean) => {
                          if (checked) {
                            addToArray('demographics', 'gender', gender.label);
                          } else {
                            removeFromArray('demographics', 'gender', gender.label);
                          }
                        }}
                      />
                      <Label className="text-sm">{formatOptionLabel(gender)}</Label>
                    </div>
                  )) : (
                    <p className="text-sm text-muted-foreground">No gender values found in the current registry snapshot.</p>
                  )}
                </div>
              </div>

              <div>
                <Label>Nationality</Label>
                <Select
                  onValueChange={(value: string) => addToArray('demographics', 'nationality', value)}
                  disabled={availableNationalities.length === 0}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Add nationality criteria" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableNationalities.length > 0 ? availableNationalities.map((nationality) => (
                      <SelectItem key={nationality.label} value={nationality.label}>{formatOptionLabel(nationality)}</SelectItem>
                    )) : (
                      <SelectItem value="no-nationality-options" disabled>No meaningful nationality values available</SelectItem>
                    )}
                  </SelectContent>
                </Select>
                {availableNationalities.length === 0 ? (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Hidden because the current dataset only contains unknown or non-segmenting nationality values.
                  </p>
                ) : null}
                <div className="flex flex-wrap gap-2 mt-2">
                  {criteria.demographics.nationality.map((nationality) => (
                    <Badge key={nationality} variant="secondary">
                      {nationality}
                      <button
                        onClick={() => removeFromArray('demographics', 'nationality', nationality)}
                        className="ml-2 text-xs"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="clinical" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Clinical Criteria</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Diagnoses</Label>
                <Select
                  onValueChange={(value: string) => addToArray('clinical', 'diagnoses', value)}
                  disabled={availableDiagnoses.length === 0}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Add diagnosis criteria" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableDiagnoses.length > 0 ? availableDiagnoses.map((diagnosis) => (
                      <SelectItem key={diagnosis.label} value={diagnosis.label}>{formatOptionLabel(diagnosis)}</SelectItem>
                    )) : (
                      <SelectItem value="no-diagnosis-options" disabled>No diagnosis values available</SelectItem>
                    )}
                  </SelectContent>
                </Select>
                <div className="flex flex-wrap gap-2 mt-2">
                  {criteria.clinical.diagnoses.map((diagnosis) => (
                    <Badge key={diagnosis} variant="default">
                      {diagnosis}
                      <button
                        onClick={() => removeFromArray('clinical', 'diagnoses', diagnosis)}
                        className="ml-2 text-xs"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <Label>Risk Factors</Label>
                <Select
                  onValueChange={(value: string) => addToArray('clinical', 'riskFactors', value)}
                  disabled={availableRiskFactors.length === 0}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Add risk factor criteria" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableRiskFactors.length > 0 ? availableRiskFactors.map((factor) => (
                      <SelectItem key={factor.label} value={factor.label}>{formatOptionLabel(factor)}</SelectItem>
                    )) : (
                      <SelectItem value="no-risk-factor-options" disabled>No risk factor values available</SelectItem>
                    )}
                  </SelectContent>
                </Select>
                <div className="flex flex-wrap gap-2 mt-2">
                  {criteria.clinical.riskFactors.map((factor) => (
                    <Badge key={factor} variant="outline">
                      {factor}
                      <button
                        onClick={() => removeFromArray('clinical', 'riskFactors', factor)}
                        className="ml-2 text-xs"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="temporal" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Temporal Constraints</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Enrollment Start Date</Label>
                  <Input
                    type="date"
                    value={criteria.temporal.enrollmentPeriod[0]}
                    onChange={(e) => updateCriteria('temporal', 'enrollmentPeriod', [e.target.value, criteria.temporal.enrollmentPeriod[1]])}
                  />
                </div>
                <div>
                  <Label>Enrollment End Date</Label>
                  <Input
                    type="date"
                    value={criteria.temporal.enrollmentPeriod[1]}
                    onChange={(e) => updateCriteria('temporal', 'enrollmentPeriod', [criteria.temporal.enrollmentPeriod[0], e.target.value])}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="data" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Data Requirements</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Required Data Types</Label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-2">
                  {availableDataTypes.length > 0 ? availableDataTypes.map((dataType) => (
                    <div key={dataType.label} className="flex items-center space-x-2">
                      <Checkbox
                        checked={criteria.dataAvailability.requiredData.includes(dataType.label)}
                        onCheckedChange={(checked: boolean) => {
                          if (checked) {
                            addToArray('dataAvailability', 'requiredData', dataType.label);
                          } else {
                            removeFromArray('dataAvailability', 'requiredData', dataType.label);
                          }
                        }}
                      />
                      <Label className="text-sm">{formatOptionLabel(dataType)}</Label>
                    </div>
                  )) : (
                    <p className="text-sm text-muted-foreground">No data-availability facets narrow this registry right now.</p>
                  )}
                </div>
              </div>

              <div>
                <Label>Minimum Data Completeness: {criteria.dataAvailability.minimumCompleteness > 0 ? `${criteria.dataAvailability.minimumCompleteness}%` : 'Off'}</Label>
                <Slider
                  value={[criteria.dataAvailability.minimumCompleteness]}
                  onValueChange={(value: number[]) => updateCriteria('dataAvailability', 'minimumCompleteness', value[0])}
                  max={100}
                  min={0}
                  step={5}
                  className="mt-2"
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  Leave this at 0 unless you explicitly want to exclude sparse records.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="geographic" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Geographic Constraints</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Locations</Label>
                <Select
                  onValueChange={(value: string) => addToArray('geographic', 'regions', value)}
                  disabled={availableRegions.length === 0}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Add location or city category" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableRegions.length > 0 ? availableRegions.map((region) => (
                      <SelectItem key={region.label} value={region.label}>{formatOptionLabel(region)}</SelectItem>
                    )) : (
                      <SelectItem value="no-region-options" disabled>No location values available</SelectItem>
                    )}
                  </SelectContent>
                </Select>
                <div className="flex flex-wrap gap-2 mt-2">
                  {criteria.geographic.regions.map((region) => (
                    <Badge key={region} variant="secondary">
                      {region}
                      <button
                        onClick={() => removeFromArray('geographic', 'regions', region)}
                        className="ml-2 text-xs"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center space-x-2">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                    <span>Query Results</span>
                  </CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">
                    {queryExecuted ? `${patients.length} patients matched your criteria` : "No query executed yet"}
                  </p>
                </div>
                {queryExecuted && (
                  <div className="flex space-x-2">
                    <Button onClick={handleDownloadCSV}>
                      <Download className="h-4 w-4 mr-2" />
                      Download CSV
                    </Button>
                    <Button variant="outline" onClick={handleDownloadJSON}>
                      <Download className="h-4 w-4 mr-2" />
                      Download JSON
                    </Button>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {queryLoading ? (
                <div className="space-y-5">
                  <div className="cohort-results-skeleton-table rounded-lg border p-4">
                    <div className="grid grid-cols-7 gap-3 border-b pb-3">
                      <div className="skeleton-block h-4 rounded-full" />
                      <div className="skeleton-block h-4 rounded-full" />
                      <div className="skeleton-block h-4 rounded-full" />
                      <div className="skeleton-block h-4 rounded-full" />
                      <div className="skeleton-block h-4 rounded-full" />
                      <div className="skeleton-block h-4 rounded-full" />
                      <div className="skeleton-block h-4 rounded-full" />
                    </div>
                    <div className="space-y-3 pt-4">
                      {Array.from({ length: 5 }).map((_, index) => (
                        <div key={index} className="grid grid-cols-7 gap-3">
                          <div className="skeleton-block h-5 rounded-full" />
                          <div className="skeleton-block h-5 rounded-full" />
                          <div className="skeleton-block h-5 rounded-full" />
                          <div className="skeleton-block h-5 rounded-full" />
                          <div className="skeleton-block h-5 rounded-full" />
                          <div className="skeleton-block h-5 rounded-full" />
                          <div className="skeleton-block h-5 rounded-full" />
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    {Array.from({ length: 3 }).map((_, index) => (
                      <Card key={index}>
                        <CardContent className="p-4">
                          <div className="space-y-3 text-center">
                            <div className="skeleton-block mx-auto h-8 w-20 rounded-2xl" />
                            <div className="skeleton-block mx-auto h-4 w-32 rounded-full" />
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Query Metadata</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {Array.from({ length: 4 }).map((_, index) => (
                        <div key={index} className="flex items-center justify-between gap-4">
                          <div className="skeleton-block h-4 w-28 rounded-full" />
                          <div className="skeleton-block h-4 w-40 rounded-full" />
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </div>
              ) : queryExecuted ? (
                <div className="space-y-4">
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-muted">
                        <tr>
                          <th className="text-left p-3 font-medium">DNA ID</th>
                          <th className="text-left p-3 font-medium">Age</th>
                          <th className="text-left p-3 font-medium">Gender</th>
                          <th className="text-left p-3 font-medium">Nationality</th>
                          <th className="text-left p-3 font-medium">Enrollment Date</th>
                          <th className="text-left p-3 font-medium">Data Completeness</th>
                          <th className="text-left p-3 font-medium">Echo EF</th>
                        </tr>
                      </thead>
                      <tbody>
                        {patients.map((patient, index) => (
                          <tr key={patient.dna_id} className={index % 2 === 0 ? "bg-white" : "bg-muted/30"}>
                            <td className="p-3 font-mono text-sm text-[#00a2ddff]">{patient.dna_id}</td>
                            <td className="p-3">{patient.age ?? 'N/A'}</td>
                            <td className="p-3">{patient.gender ?? 'N/A'}</td>
                            <td className="p-3 max-w-xs truncate" title={patient.nationality ?? ''}>{patient.nationality ?? 'N/A'}</td>
                            <td className="p-3">{patient.enrollment_date ?? 'N/A'}</td>
                            <td className="p-3">
                              <div className="flex items-center space-x-2">
                                <div className="w-16 bg-gray-200 rounded-full h-2">
                                  <div 
                                    className="bg-blue-500 h-2 rounded-full" 
                                    style={{ width: `${patient.data_completeness}%` }}
                                  />
                                </div>
                                <span className="text-sm">{patient.data_completeness}%</span>
                              </div>
                            </td>
                            <td className="p-3">
                              {patient.echo_ef ? `${patient.echo_ef}%` : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardContent className="p-4">
                        <div className="text-center">
                          <p className="text-2xl" style={{ color: '#00a2dd' }}>{patients.length}</p>
                          <p className="text-sm text-muted-foreground">Total Patients</p>
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <div className="text-center">
                          <p className="text-2xl" style={{ color: '#efb01b' }}>
                            {averageCompleteness}%
                          </p>
                          <p className="text-sm text-muted-foreground">Avg Data Completeness</p>
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <div className="text-center">
                          <p className="text-2xl" style={{ color: '#e9322b' }}>
                            {averageAge}
                          </p>
                          <p className="text-sm text-muted-foreground">Avg Age (years)</p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Query Metadata</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Cohort Name:</span>
                        <span className="font-medium">{cohortName || "Unnamed Cohort"}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Executed:</span>
                        <span className="font-medium">{new Date().toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Dataset:</span>
                        <span className="font-medium">{DATASET_OPTIONS.find((option) => option.value === selectedDataset)?.label}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Age Range:</span>
                        <span className="font-medium">
                          {criteria.demographics.ageRange[0] === DEFAULT_AGE_RANGE[0] && criteria.demographics.ageRange[1] === DEFAULT_AGE_RANGE[1]
                            ? 'All ages'
                            : `${criteria.demographics.ageRange[0]} - ${criteria.demographics.ageRange[1]} years`}
                        </span>
                      </div>
                      {criteria.clinical.diagnoses.length > 0 && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Diagnoses:</span>
                          <span className="font-medium">{criteria.clinical.diagnoses.join(", ")}</span>
                        </div>
                      )}
                      {criteria.dataAvailability.requiredData.length > 0 && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Required Data:</span>
                          <span className="font-medium">{criteria.dataAvailability.requiredData.join(", ")}</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Database className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No Query Results Yet</h3>
                  <p className="text-muted-foreground mb-4">
                    Execute a query with your selected criteria to see patient results here
                  </p>
                  <Button onClick={handleExecuteQuery} disabled={queryLoading}>
                    {queryLoading ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4 mr-2" />
                    )}
                    {queryLoading ? "Querying..." : "Execute Query"}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button className="w-full" onClick={handleExecuteQuery} disabled={queryLoading}>
              {queryLoading ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Play className="h-4 w-4 mr-2" />
              )}
              {queryLoading ? "Querying..." : "Execute Query"}
            </Button>
            <Button variant="outline" className="w-full" onClick={handleSaveCohort}>
              <Save className="h-4 w-4 mr-2" />
              Save Cohort
            </Button>
            <Button variant="outline" className="w-full" onClick={handleExportCriteria}>
              <Download className="h-4 w-4 mr-2" />
              Export Criteria
            </Button>
            <Button variant="outline" className="w-full" onClick={handleViewOnMap}>
              <Map className="h-4 w-4 mr-2" />
              View on Map
            </Button>
            {actionMessage ? (
              <p className="text-sm text-muted-foreground">{actionMessage}</p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Saved Cohorts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {savedCohorts.map((cohort) => (
              <div key={cohort.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <div className="font-medium">{cohort.name}</div>
                  <div className="text-sm text-muted-foreground">
                    {cohort.size.toLocaleString()} patients • {cohort.lastModified}
                  </div>
                </div>
                <Button variant="ghost" size="sm" onClick={() => handleLoadCohort(cohort)}>
                  Load
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}