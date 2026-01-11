import { useState, useMemo } from "react";
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
import { useRegistryOverview } from "../hooks/useAnalytics";
import type { Patient } from "../api/types";
import type { PatientsQueryParams } from "../api/patients";

interface CohortCriteria {
  demographics: {
    ageRange: [number, number];
    gender: string[];
    ethnicity: string[];
  };
  clinical: {
    diagnoses: string[];
    riskFactors: string[];
    biomarkerRanges: Record<string, [number, number]>;
  };
  temporal: {
    enrollmentPeriod: [string, string];
    followUpDuration: string;
  };
  dataAvailability: {
    requiredData: string[];
    minimumCompleteness: number;
  };
  geographic: {
    regions: string[];
    sites: string[];
  };
}

export function CohortBuilder() {
  const [cohortName, setCohortName] = useState("");
  const [description, setDescription] = useState("");
  const [queryExecuted, setQueryExecuted] = useState(false);
  const [criteria, setCriteria] = useState<CohortCriteria>({
    demographics: {
      ageRange: [18, 90],
      gender: [],
      ethnicity: []
    },
    clinical: {
      diagnoses: [],
      riskFactors: [],
      biomarkerRanges: {}
    },
    temporal: {
      enrollmentPeriod: ["", ""],
      followUpDuration: "any"
    },
    dataAvailability: {
      requiredData: [],
      minimumCompleteness: 70
    },
    geographic: {
      regions: [],
      sites: []
    }
  });

  // Build query params from all criteria (memoized for performance)
  const estimateParams = useMemo((): PatientsQueryParams => {
    const params: PatientsQueryParams = {
      // Demographics
      ageMin: criteria.demographics.ageRange[0],
      ageMax: criteria.demographics.ageRange[1],
      gender: criteria.demographics.gender.length > 0 ? criteria.demographics.gender[0] : undefined,
      
      // Temporal filters
      enrollmentDateFrom: criteria.temporal.enrollmentPeriod[0] || undefined,
      enrollmentDateTo: criteria.temporal.enrollmentPeriod[1] || undefined,
      
      // Data availability filters
      minDataCompleteness: criteria.dataAvailability.minimumCompleteness,
      
      // Geographic filters
      region: criteria.geographic.regions.length > 0 ? criteria.geographic.regions[0] : undefined,
    };
    
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
    if (criteria.clinical.diagnoses.includes('Essential Hypertension')) params.hasHypertension = true;
    
    // Ethnicity as nationality
    if (criteria.demographics.ethnicity.length > 0) params.nationality = criteria.demographics.ethnicity[0];
    
    return params;
  }, [criteria]);

  // Use hooks for API integration
  const { mutate: executeQuery, isLoading: queryLoading, data: queryData } = useCohortQuery();
  const { data: estimateData, isLoading: estimateLoading } = useCohortEstimate(estimateParams);
  const { mutate: downloadCohort } = useDownloadCohort();
  
  // Get total patient count from registry overview
  const { data: overview } = useRegistryOverview();
  const totalPatients = overview?.totalPatients ?? 0;

  const estimatedSize = estimateData?.count || 0;
  
  // Use patients from hook or empty array
  const patients = queryData || [];
  
  const [savedCohorts, setSavedCohorts] = useState([
    { id: 1, name: "CAD High Risk", size: 389, lastModified: "2024-12-15" },
    { id: 2, name: "Heart Failure Cohort", size: 156, lastModified: "2024-12-10" },
    { id: 3, name: "Genomics Complete", size: 1108, lastModified: "2024-12-08" }
  ]);

  const availableDiagnoses = [
    "Essential Hypertension",
    "Coronary Artery Disease", 
    "Heart Failure",
    "Arrhythmia",
    "Atherosclerosis",
    "Myocardial Infarction",
    "Stroke",
    "Peripheral Artery Disease"
  ];

  const availableRiskFactors = [
    "Diabetes",
    "Smoking",
    "Family History",
    "Obesity",
    "Sedentary Lifestyle",
    "High Blood Pressure",
    "High Cholesterol"
  ];

  const availableDataTypes = [
    "Genomics",
    "Biomarkers", 
    "Imaging",
    "Clinical Labs",
    "Demographics",
    "Medications",
    "Outcomes"
  ];

  const availableRegions = [
    "North America",
    "Europe", 
    "Asia",
    "South America",
    "Africa",
    "Oceania"
  ];

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

  // Mock patient data for query results
  const mockQueryResults = [
    {
      mrn: "CVD-001247",
      name: "Sarah Johnson",
      age: 62,
      gender: "Female",
      diagnosis: "Essential Hypertension, Mixed Dyslipidemia",
      enrollmentDate: "2024-01-15",
      dataCompleteness: 94,
      studyPhase: "follow-up"
    },
    {
      mrn: "CVD-001248",
      name: "Michael Chen",
      age: 58,
      gender: "Male",
      diagnosis: "Coronary Atherosclerosis (I25.10)",
      enrollmentDate: "2024-02-20",
      dataCompleteness: 98,
      studyPhase: "baseline"
    },
    {
      mrn: "CVD-001249",
      name: "Robert Williams",
      age: 71,
      gender: "Male",
      diagnosis: "Heart Failure with Reduced EF (I50.1)",
      enrollmentDate: "2023-11-10",
      dataCompleteness: 87,
      studyPhase: "long-term"
    },
    {
      mrn: "CVD-001250",
      name: "Emily Davis",
      age: 45,
      gender: "Female",
      diagnosis: "Atrial Fibrillation (I48.91)",
      enrollmentDate: "2024-03-05",
      dataCompleteness: 85,
      studyPhase: "completed"
    },
    {
      mrn: "CVD-001251",
      name: "Patricia Martinez",
      age: 67,
      gender: "Female",
      diagnosis: "Coronary Atherosclerosis, Multiple Vessels",
      enrollmentDate: "2023-08-18",
      dataCompleteness: 96,
      studyPhase: "long-term"
    },
  ];

  const handleExecuteQuery = async () => {
    await executeQuery({ ...estimateParams, limit: 500 });
    setQueryExecuted(true);
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

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="h-5 w-5" />
            <span>Advanced Cohort Builder</span>
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Build sophisticated patient cohorts with multi-dimensional filtering and temporal constraints
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Cohort Name</Label>
              <Input
                value={cohortName}
                onChange={(e) => setCohortName(e.target.value)}
                placeholder="Enter cohort name"
              />
            </div>
            <div className="flex items-end">
              <div className="text-center">
                <Label className="text-sm text-muted-foreground">Estimated Size</Label>
                {estimateLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin mx-auto mt-2" />
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

      <Tabs defaultValue="demographics" className="space-y-4">
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="demographics">Demographics</TabsTrigger>
          <TabsTrigger value="clinical">Clinical</TabsTrigger>
          <TabsTrigger value="temporal">Temporal</TabsTrigger>
          <TabsTrigger value="data">Data Requirements</TabsTrigger>
          <TabsTrigger value="geographic">Geographic</TabsTrigger>
          <TabsTrigger value="trials">Clinical Trials</TabsTrigger>
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
                <Label>Age Range: {criteria.demographics.ageRange[0]} - {criteria.demographics.ageRange[1]} years</Label>
                <Slider
                  value={criteria.demographics.ageRange}
                  onValueChange={(value: number[]) => updateCriteria('demographics', 'ageRange', value)}
                  max={100}
                  min={0}
                  step={1}
                  className="mt-2"
                />
              </div>

              <div>
                <Label>Gender</Label>
                <div className="flex space-x-2 mt-2">
                  {['Male', 'Female', 'Other'].map((gender) => (
                    <div key={gender} className="flex items-center space-x-2">
                      <Checkbox
                        checked={criteria.demographics.gender.includes(gender)}
                        onCheckedChange={(checked: boolean) => {
                          if (checked) {
                            addToArray('demographics', 'gender', gender);
                          } else {
                            removeFromArray('demographics', 'gender', gender);
                          }
                        }}
                      />
                      <Label className="text-sm">{gender}</Label>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <Label>Ethnicity</Label>
                <Select
                  onValueChange={(value: string) => addToArray('demographics', 'ethnicity', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Add ethnicity criteria" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="white">White/Caucasian</SelectItem>
                    <SelectItem value="black">Black/African American</SelectItem>
                    <SelectItem value="hispanic">Hispanic/Latino</SelectItem>
                    <SelectItem value="asian">Asian</SelectItem>
                    <SelectItem value="native">Native American</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
                <div className="flex flex-wrap gap-2 mt-2">
                  {criteria.demographics.ethnicity.map((ethnicity) => (
                    <Badge key={ethnicity} variant="secondary">
                      {ethnicity}
                      <button
                        onClick={() => removeFromArray('demographics', 'ethnicity', ethnicity)}
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
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Add diagnosis criteria" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableDiagnoses.map((diagnosis) => (
                      <SelectItem key={diagnosis} value={diagnosis}>{diagnosis}</SelectItem>
                    ))}
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
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Add risk factor criteria" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableRiskFactors.map((factor) => (
                      <SelectItem key={factor} value={factor}>{factor}</SelectItem>
                    ))}
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

              <div>
                <Label>Protein Biomarker Ranges</Label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                  <div>
                    <Label className="text-sm">Troponin I (ng/L)</Label>
                    <div className="flex space-x-2">
                      <Input placeholder="Min" type="number" />
                      <Input placeholder="Max" type="number" />
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm">BNP (pg/mL)</Label>
                    <div className="flex space-x-2">
                      <Input placeholder="Min" type="number" />
                      <Input placeholder="Max" type="number" />
                    </div>
                  </div>
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

              <div>
                <Label>Minimum Follow-up Duration</Label>
                <Select
                  value={criteria.temporal.followUpDuration}
                  onValueChange={(value: string) => updateCriteria('temporal', 'followUpDuration', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="any">Any duration</SelectItem>
                    <SelectItem value="3months">3+ months</SelectItem>
                    <SelectItem value="6months">6+ months</SelectItem>
                    <SelectItem value="1year">1+ year</SelectItem>
                    <SelectItem value="2years">2+ years</SelectItem>
                    <SelectItem value="5years">5+ years</SelectItem>
                  </SelectContent>
                </Select>
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
                  {availableDataTypes.map((dataType) => (
                    <div key={dataType} className="flex items-center space-x-2">
                      <Checkbox
                        checked={criteria.dataAvailability.requiredData.includes(dataType)}
                        onCheckedChange={(checked: boolean) => {
                          if (checked) {
                            addToArray('dataAvailability', 'requiredData', dataType);
                          } else {
                            removeFromArray('dataAvailability', 'requiredData', dataType);
                          }
                        }}
                      />
                      <Label className="text-sm">{dataType}</Label>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <Label>Minimum Data Completeness: {criteria.dataAvailability.minimumCompleteness}%</Label>
                <Slider
                  value={[criteria.dataAvailability.minimumCompleteness]}
                  onValueChange={(value: number[]) => updateCriteria('dataAvailability', 'minimumCompleteness', value[0])}
                  max={100}
                  min={0}
                  step={5}
                  className="mt-2"
                />
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
                <Label>Regions</Label>
                <Select
                  onValueChange={(value: string) => addToArray('geographic', 'regions', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Add geographic region" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableRegions.map((region) => (
                      <SelectItem key={region} value={region}>{region}</SelectItem>
                    ))}
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

              <div>
                <Label>Specific Sites</Label>
                <Input placeholder="Enter site names or IDs" />
                <p className="text-xs text-muted-foreground mt-1">
                  Leave empty to include all sites in selected regions
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trials" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Beaker className="h-5 w-5 text-primary" />
                <span>Registry-Based Clinical Trials Module</span>
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                Multicenter trial setup, eligibility screening, patient enrollment, and progress tracking
              </p>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="registry" className="space-y-4">
                <TabsList className="grid w-full grid-cols-5">
                  <TabsTrigger value="registry">Trial Registry</TabsTrigger>
                  <TabsTrigger value="eligibility">Eligibility Engine</TabsTrigger>
                  <TabsTrigger value="flagging">Patient Flagging</TabsTrigger>
                  <TabsTrigger value="dashboard">Progress Dashboard</TabsTrigger>
                  <TabsTrigger value="consent">Consent Workflow</TabsTrigger>
                </TabsList>

                <TabsContent value="registry" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Active Trials</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium">ASCEND-CVD</h4>
                            <Badge className="bg-green-100 text-green-800">Recruiting</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mb-3">
                            Novel antiplatelet therapy for high-risk CAD patients
                          </p>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            <div>
                              <span className="text-muted-foreground">NCT ID:</span>
                              <p className="font-medium">NCT05847293</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Phase:</span>
                              <p className="font-medium">Phase III</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Sites:</span>
                              <p className="font-medium">12 centers</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Enrolled:</span>
                              <p className="font-medium">187 / 500</p>
                            </div>
                          </div>
                          <div className="mt-3 flex space-x-2">
                            <Button size="sm" variant="outline" className="flex-1">
                              View Details
                            </Button>
                            <Button size="sm" className="flex-1">
                              Manage
                            </Button>
                          </div>
                        </div>

                        <div className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium">BIOMARK-HF</h4>
                            <Badge className="bg-blue-100 text-blue-800">Enrolling</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mb-3">
                            Protein biomarker-guided therapy in heart failure patients
                          </p>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            <div>
                              <span className="text-muted-foreground">NCT ID:</span>
                              <p className="font-medium">NCT05923154</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Phase:</span>
                              <p className="font-medium">Phase II/III</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Sites:</span>
                              <p className="font-medium">8 centers</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Enrolled:</span>
                              <p className="font-medium">94 / 300</p>
                            </div>
                          </div>
                          <div className="mt-3 flex space-x-2">
                            <Button size="sm" variant="outline" className="flex-1">
                              View Details
                            </Button>
                            <Button size="sm" className="flex-1">
                              Manage
                            </Button>
                          </div>
                        </div>

                        <div className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium">PRECISION-AF</h4>
                            <Badge variant="outline">Planning</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground mb-3">
                            Genomics-guided anticoagulation in atrial fibrillation
                          </p>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            <div>
                              <span className="text-muted-foreground">NCT ID:</span>
                              <p className="font-medium">Pending</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Phase:</span>
                              <p className="font-medium">Phase III</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Sites:</span>
                              <p className="font-medium">15 centers</p>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Target:</span>
                              <p className="font-medium">0 / 600</p>
                            </div>
                          </div>
                          <div className="mt-3 flex space-x-2">
                            <Button size="sm" variant="outline" className="flex-1">
                              View Details
                            </Button>
                            <Button size="sm" className="flex-1">
                              Manage
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Create New Trial</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <Label>Trial Name</Label>
                          <Input placeholder="Enter trial name" />
                        </div>
                        <div>
                          <Label>NCT ID (Optional)</Label>
                          <Input placeholder="NCT########" />
                        </div>
                        <div>
                          <Label>Trial Phase</Label>
                          <Select>
                            <SelectTrigger>
                              <SelectValue placeholder="Select phase" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="phase1">Phase I</SelectItem>
                              <SelectItem value="phase2">Phase II</SelectItem>
                              <SelectItem value="phase3">Phase III</SelectItem>
                              <SelectItem value="phase4">Phase IV</SelectItem>
                              <SelectItem value="observational">Observational</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>Principal Investigator</Label>
                          <Input placeholder="Enter PI name" />
                        </div>
                        <div>
                          <Label>Target Enrollment</Label>
                          <Input type="number" placeholder="Number of participants" />
                        </div>
                        <div>
                          <Label>Study Type</Label>
                          <Select>
                            <SelectTrigger>
                              <SelectValue placeholder="Select study type" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="interventional">Interventional</SelectItem>
                              <SelectItem value="observational">Observational</SelectItem>
                              <SelectItem value="expanded-access">Expanded Access</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <Button className="w-full">
                          <Save className="h-4 w-4 mr-2" />
                          Create Trial Registry
                        </Button>
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="eligibility" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Eligibility Criteria Engine</CardTitle>
                      <p className="text-sm text-muted-foreground">Define inclusion and exclusion criteria for automated screening</p>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="border rounded-lg p-4">
                          <h4 className="font-medium mb-3 flex items-center space-x-2">
                            <CheckCircle2 className="h-4 w-4 text-green-600" />
                            <span>Inclusion Criteria</span>
                          </h4>
                          <div className="space-y-3">
                            <div className="flex items-center justify-between p-2 bg-green-50 rounded">
                              <span className="text-sm">Age 18-75 years</span>
                              <Button variant="ghost" size="sm">×</Button>
                            </div>
                            <div className="flex items-center justify-between p-2 bg-green-50 rounded">
                              <span className="text-sm">Documented CAD diagnosis</span>
                              <Button variant="ghost" size="sm">×</Button>
                            </div>
                            <div className="flex items-center justify-between p-2 bg-green-50 rounded">
                              <span className="text-sm">LVEF ≥ 40%</span>
                              <Button variant="ghost" size="sm">×</Button>
                            </div>
                            <div className="flex items-center justify-between p-2 bg-green-50 rounded">
                              <span className="text-sm">Baseline troponin &lt; 100 ng/L</span>
                              <Button variant="ghost" size="sm">×</Button>
                            </div>
                            <Button variant="outline" size="sm" className="w-full">
                              + Add Inclusion Criterion
                            </Button>
                          </div>
                        </div>

                        <div className="border rounded-lg p-4">
                          <h4 className="font-medium mb-3 flex items-center space-x-2">
                            <AlertCircle className="h-4 w-4 text-red-600" />
                            <span>Exclusion Criteria</span>
                          </h4>
                          <div className="space-y-3">
                            <div className="flex items-center justify-between p-2 bg-red-50 rounded">
                              <span className="text-sm">Recent MI (&lt; 30 days)</span>
                              <Button variant="ghost" size="sm">×</Button>
                            </div>
                            <div className="flex items-center justify-between p-2 bg-red-50 rounded">
                              <span className="text-sm">Active bleeding disorder</span>
                              <Button variant="ghost" size="sm">×</Button>
                            </div>
                            <div className="flex items-center justify-between p-2 bg-red-50 rounded">
                              <span className="text-sm">Severe renal impairment (eGFR &lt; 30)</span>
                              <Button variant="ghost" size="sm">×</Button>
                            </div>
                            <div className="flex items-center justify-between p-2 bg-red-50 rounded">
                              <span className="text-sm">Pregnancy or breastfeeding</span>
                              <Button variant="ghost" size="sm">×</Button>
                            </div>
                            <Button variant="outline" size="sm" className="w-full">
                              + Add Exclusion Criterion
                            </Button>
                          </div>
                        </div>
                      </div>

                      <div className="border-t pt-4">
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="font-medium">Eligibility Summary</h4>
                          <Button variant="outline" size="sm">
                            <Play className="h-4 w-4 mr-2" />
                            Run Screening
                          </Button>
                        </div>
                        <div className="grid grid-cols-3 gap-4">
                          <div className="text-center p-3 border rounded-lg">
                            <p className="text-2xl text-green-600">{totalPatients.toLocaleString()}</p>
                            <p className="text-sm text-muted-foreground">Potentially Eligible</p>
                          </div>
                          <div className="text-center p-3 border rounded-lg">
                            <p className="text-2xl text-yellow-600">{Math.round(totalPatients * 0.37).toLocaleString()}</p>
                            <p className="text-sm text-muted-foreground">Partial Match</p>
                          </div>
                          <div className="text-center p-3 border rounded-lg">
                            <p className="text-2xl text-red-600">0</p>
                            <p className="text-sm text-muted-foreground">Not Eligible</p>
                          </div>
                        </div>
                      </div>

                      <Button className="w-full">
                        <Save className="h-4 w-4 mr-2" />
                        Save Eligibility Criteria
                      </Button>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="flagging" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Automated Patient Flagging</CardTitle>
                      <p className="text-sm text-muted-foreground">Real-time identification of eligible patients</p>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="border rounded-lg p-4 bg-blue-50">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-medium">Auto-Screening Status</h4>
                          <Badge className="bg-green-100 text-green-800">Active</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          Automatic screening runs daily at 2:00 AM for all active trials
                        </p>
                      </div>

                      <div className="space-y-3">
                        <h4 className="font-medium">Recently Flagged Patients (ASCEND-CVD)</h4>
                        
                        <div className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-3">
                              <UserCheck className="h-5 w-5 text-green-600" />
                              <div>
                                <p className="font-medium">MYF-002458 - James Anderson</p>
                                <p className="text-sm text-muted-foreground">Age 58, Male • CAD diagnosis confirmed</p>
                              </div>
                            </div>
                            <Badge className="bg-green-100 text-green-800">Eligible</Badge>
                          </div>
                          <div className="mt-3 flex items-center justify-between text-sm">
                            <div className="flex space-x-4">
                              <span className="text-muted-foreground">Flagged: Dec 15, 2024</span>
                              <span className="text-muted-foreground">Match: 100%</span>
                            </div>
                            <div className="flex space-x-2">
                              <Button size="sm" variant="outline">Review</Button>
                              <Button size="sm">Contact</Button>
                            </div>
                          </div>
                        </div>

                        <div className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-3">
                              <UserCheck className="h-5 w-5 text-green-600" />
                              <div>
                                <p className="font-medium">MYF-003721 - Maria Rodriguez</p>
                                <p className="text-sm text-muted-foreground">Age 64, Female • Recent angioplasty</p>
                              </div>
                            </div>
                            <Badge className="bg-green-100 text-green-800">Eligible</Badge>
                          </div>
                          <div className="mt-3 flex items-center justify-between text-sm">
                            <div className="flex space-x-4">
                              <span className="text-muted-foreground">Flagged: Dec 14, 2024</span>
                              <span className="text-muted-foreground">Match: 95%</span>
                            </div>
                            <div className="flex space-x-2">
                              <Button size="sm" variant="outline">Review</Button>
                              <Button size="sm">Contact</Button>
                            </div>
                          </div>
                        </div>

                        <div className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-3">
                              <AlertCircle className="h-5 w-5 text-yellow-600" />
                              <div>
                                <p className="font-medium">MYF-001892 - David Chen</p>
                                <p className="text-sm text-muted-foreground">Age 72, Male • Borderline LVEF</p>
                              </div>
                            </div>
                            <Badge className="bg-yellow-100 text-yellow-800">Review Required</Badge>
                          </div>
                          <div className="mt-3 flex items-center justify-between text-sm">
                            <div className="flex space-x-4">
                              <span className="text-muted-foreground">Flagged: Dec 14, 2024</span>
                              <span className="text-muted-foreground">Match: 85%</span>
                            </div>
                            <div className="flex space-x-2">
                              <Button size="sm" variant="outline">Review</Button>
                              <Button size="sm">Contact</Button>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="flex space-x-2">
                        <Button className="flex-1">
                          <Download className="h-4 w-4 mr-2" />
                          Export Flagged List
                        </Button>
                        <Button variant="outline" className="flex-1">
                          <Filter className="h-4 w-4 mr-2" />
                          Filter Patients
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="dashboard" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-muted-foreground">Total Enrolled</p>
                            <p className="text-2xl">281</p>
                            <p className="text-sm text-green-600">+12 this week</p>
                          </div>
                          <Users className="h-8 w-8 text-blue-500" />
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-muted-foreground">Screening</p>
                            <p className="text-2xl">67</p>
                            <p className="text-sm text-yellow-600">Pending review</p>
                          </div>
                          <ClipboardList className="h-8 w-8 text-yellow-500" />
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-muted-foreground">Enrollment Rate</p>
                            <p className="text-2xl">78%</p>
                            <p className="text-sm text-green-600">On target</p>
                          </div>
                          <TrendingUp className="h-8 w-8 text-green-500" />
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Trial Progress Dashboard</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-3">
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium">ASCEND-CVD</span>
                            <span className="text-sm text-muted-foreground">187 / 500 (37%)</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-3">
                            <div className="bg-blue-500 h-3 rounded-full" style={{ width: '37%' }} />
                          </div>
                        </div>

                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium">BIOMARK-HF</span>
                            <span className="text-sm text-muted-foreground">94 / 300 (31%)</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-3">
                            <div className="bg-green-500 h-3 rounded-full" style={{ width: '31%' }} />
                          </div>
                        </div>

                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium">PRECISION-AF</span>
                            <span className="text-sm text-muted-foreground">0 / 600 (0%)</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-3">
                            <div className="bg-gray-400 h-3 rounded-full" style={{ width: '0%' }} />
                          </div>
                        </div>
                      </div>

                      <div className="border-t pt-4">
                        <h4 className="font-medium mb-3">Site Performance (ASCEND-CVD)</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex items-center justify-between p-2 border rounded">
                            <span>Springfield Medical Center</span>
                            <div className="flex items-center space-x-2">
                              <span className="text-muted-foreground">52 enrolled</span>
                              <Badge className="bg-green-100 text-green-800">Top performer</Badge>
                            </div>
                          </div>
                          <div className="flex items-center justify-between p-2 border rounded">
                            <span>Metro Heart Institute</span>
                            <div className="flex items-center space-x-2">
                              <span className="text-muted-foreground">38 enrolled</span>
                              <Badge variant="outline">On track</Badge>
                            </div>
                          </div>
                          <div className="flex items-center justify-between p-2 border rounded">
                            <span>Regional Cardiology Center</span>
                            <div className="flex items-center space-x-2">
                              <span className="text-muted-foreground">27 enrolled</span>
                              <Badge variant="outline">On track</Badge>
                            </div>
                          </div>
                        </div>
                      </div>

                      <Button className="w-full">
                        <FileText className="h-4 w-4 mr-2" />
                        Generate Progress Report
                      </Button>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="consent" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Informed Consent Workflow</CardTitle>
                      <p className="text-sm text-muted-foreground">Track consent status and documentation</p>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="border rounded-lg p-4">
                        <h4 className="font-medium mb-3">Consent Document Templates</h4>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between p-3 border rounded">
                            <div>
                              <p className="font-medium text-sm">Main Study Consent Form v2.1</p>
                              <p className="text-xs text-muted-foreground">Last updated: Dec 1, 2024 • IRB approved</p>
                            </div>
                            <div className="flex space-x-2">
                              <Button size="sm" variant="outline">Preview</Button>
                              <Button size="sm">Use</Button>
                            </div>
                          </div>
                          <div className="flex items-center justify-between p-3 border rounded">
                            <div>
                              <p className="font-medium text-sm">Genetic Testing Addendum v1.0</p>
                              <p className="text-xs text-muted-foreground">Last updated: Nov 15, 2024 • IRB approved</p>
                            </div>
                            <div className="flex space-x-2">
                              <Button size="sm" variant="outline">Preview</Button>
                              <Button size="sm">Use</Button>
                            </div>
                          </div>
                          <div className="flex items-center justify-between p-3 border rounded">
                            <div>
                              <p className="font-medium text-sm">Data Sharing Authorization v1.2</p>
                              <p className="text-xs text-muted-foreground">Last updated: Oct 20, 2024 • IRB approved</p>
                            </div>
                            <div className="flex space-x-2">
                              <Button size="sm" variant="outline">Preview</Button>
                              <Button size="sm">Use</Button>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="border rounded-lg p-4">
                        <h4 className="font-medium mb-3">Consent Status Overview</h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          <div className="text-center p-3 border rounded-lg bg-green-50">
                            <p className="text-2xl text-green-600">187</p>
                            <p className="text-sm text-muted-foreground">Consented</p>
                          </div>
                          <div className="text-center p-3 border rounded-lg bg-yellow-50">
                            <p className="text-2xl text-yellow-600">23</p>
                            <p className="text-sm text-muted-foreground">Pending</p>
                          </div>
                          <div className="text-center p-3 border rounded-lg bg-blue-50">
                            <p className="text-2xl text-blue-600">8</p>
                            <p className="text-sm text-muted-foreground">In Review</p>
                          </div>
                          <div className="text-center p-3 border rounded-lg bg-red-50">
                            <p className="text-2xl text-red-600">12</p>
                            <p className="text-sm text-muted-foreground">Declined</p>
                          </div>
                        </div>
                      </div>

                      <div className="border rounded-lg p-4">
                        <h4 className="font-medium mb-3">Recent Consent Activities</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex items-center justify-between p-2 border-l-4 border-green-500 pl-3 bg-green-50">
                            <div>
                              <p className="font-medium">MYF-002458 - James Anderson</p>
                              <p className="text-xs text-muted-foreground">Signed main consent + genetic testing addendum</p>
                            </div>
                            <span className="text-xs text-muted-foreground">2 hours ago</span>
                          </div>
                          <div className="flex items-center justify-between p-2 border-l-4 border-green-500 pl-3 bg-green-50">
                            <div>
                              <p className="font-medium">MYF-003721 - Maria Rodriguez</p>
                              <p className="text-xs text-muted-foreground">Signed main consent form</p>
                            </div>
                            <span className="text-xs text-muted-foreground">5 hours ago</span>
                          </div>
                          <div className="flex items-center justify-between p-2 border-l-4 border-yellow-500 pl-3 bg-yellow-50">
                            <div>
                              <p className="font-medium">MYF-001892 - David Chen</p>
                              <p className="text-xs text-muted-foreground">Consent form sent for review</p>
                            </div>
                            <span className="text-xs text-muted-foreground">1 day ago</span>
                          </div>
                          <div className="flex items-center justify-between p-2 border-l-4 border-red-500 pl-3 bg-red-50">
                            <div>
                              <p className="font-medium">MYF-004512 - Emily Watson</p>
                              <p className="text-xs text-muted-foreground">Declined participation</p>
                            </div>
                            <span className="text-xs text-muted-foreground">2 days ago</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex space-x-2">
                        <Button className="flex-1">
                          <Download className="h-4 w-4 mr-2" />
                          Export Consent Records
                        </Button>
                        <Button variant="outline" className="flex-1">
                          <FileText className="h-4 w-4 mr-2" />
                          Audit Trail
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
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
              {queryExecuted ? (
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
                            {patients.length > 0 ? Math.round(patients.reduce((sum, p) => sum + p.data_completeness, 0) / patients.length) : 0}%
                          </p>
                          <p className="text-sm text-muted-foreground">Avg Data Completeness</p>
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <div className="text-center">
                          <p className="text-2xl" style={{ color: '#e9322b' }}>
                            {patients.length > 0 ? Math.round(patients.reduce((sum, p) => sum + (p.age || 0), 0) / patients.length) : 0}
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
                        <span className="text-muted-foreground">Age Range:</span>
                        <span className="font-medium">{criteria.demographics.ageRange[0]} - {criteria.demographics.ageRange[1]} years</span>
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
            <Button variant="outline" className="w-full">
              <Save className="h-4 w-4 mr-2" />
              Save Cohort
            </Button>
            <Button variant="outline" className="w-full">
              <Download className="h-4 w-4 mr-2" />
              Export Criteria
            </Button>
            <Button variant="outline" className="w-full">
              <Map className="h-4 w-4 mr-2" />
              View on Map
            </Button>
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
                <Button variant="ghost" size="sm">
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