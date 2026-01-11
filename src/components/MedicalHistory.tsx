import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { FileText, Calendar, Stethoscope, Activity, Plus, Download } from "lucide-react";

interface MedicalHistoryProps {
  history: {
    diagnoses: Array<{
      id: string;
      condition: string;
      icd10Code: string;
      diagnosedDate: string;
      status: 'controlled' | 'treated' | 'symptomatic' | 'stable' | 'resolved' | 'chronic';
      severity: 'Stage 1' | 'Stage 2' | 'High-Risk Category' | 'Mild MR (Grade 1)' | 'Moderate MR (Grade 2)' | 'Severe MR (Grade 3-4)' | 'Moderate Stenosis (60-70%)' | 'Severe Stenosis (>70%)' | 'Critical Stenosis (>90%)';
      category: string;
      clinicalNotes?: string;
    }>;
    procedures: Array<{
      id: string;
      name: string;
      date: string;
      facility: string;
      outcome: string;
    }>;
    tests: Array<{
      id: string;
      name: string;
      date: string;
      result: string;
      status: 'normal' | 'abnormal' | 'pending';
      notes?: string;
    }>;
    longitudinalData: Array<{
      id: string;
      date: string;
      visitType: string;
      provider: string;
      followUpStatus: 'scheduled' | 'completed' | 'overdue' | 'cancelled';
      primaryOutcome: string;
      clinicalAssessment: string;
      nextFollowUp?: string;
      interventions?: string[];
      proteinBiomarkerChanges?: string;
      functionalStatus?: string;
    }>;
  };
}

export function MedicalHistory({ history }: MedicalHistoryProps) {
  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'symptomatic': case 'abnormal': return 'destructive';
      case 'controlled': case 'treated': case 'stable': case 'normal': return 'secondary';
      case 'resolved': return 'default';
      case 'chronic': case 'pending': return 'outline';
      default: return 'outline';
    }
  };

  const getSeverityVariant = (severity: string) => {
    switch (severity) {
      case 'Severe MR (Grade 3-4)': case 'Critical Stenosis (>90%)': case 'Severe Stenosis (>70%)': 
        return 'destructive';
      case 'Stage 2': case 'Moderate MR (Grade 2)': case 'Moderate Stenosis (60-70%)': case 'High-Risk Category': 
        return 'default';
      case 'Stage 1': case 'Mild MR (Grade 1)': 
        return 'secondary';
      default: return 'outline';
    }
  };

  return (
    <Tabs defaultValue="diagnoses" className="space-y-4">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger value="diagnoses">Clinical Diagnoses</TabsTrigger>
        <TabsTrigger value="procedures">Procedures</TabsTrigger>
        <TabsTrigger value="tests">Lab Results</TabsTrigger>
        <TabsTrigger value="longitudinal">Longitudinal Follow-up</TabsTrigger>
      </TabsList>

      <TabsContent value="diagnoses" className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3>Clinical Diagnoses & Classifications</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Standardized cardiovascular diagnoses with ICD-10 codes
            </p>
          </div>
        </div>
        
        <div className="space-y-3">
          {history.diagnoses.map((diagnosis) => (
            <Card key={diagnosis.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 bg-red-100 rounded-full">
                      <Stethoscope className="h-4 w-4 text-red-600" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <h4>{diagnosis.condition}</h4>
                        <Badge variant="outline" className="text-xs font-mono">
                          {diagnosis.icd10Code}
                        </Badge>
                      </div>
                      <div className="text-sm text-muted-foreground space-y-1">
                        <p>Category: {diagnosis.category}</p>
                        <p>Diagnosed: {diagnosis.diagnosedDate}</p>
                        {diagnosis.clinicalNotes && (
                          <p className="text-xs bg-blue-50 p-2 rounded mt-2">
                            <strong>Clinical Notes:</strong> {diagnosis.clinicalNotes}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col space-y-1">
                    <Badge variant={getSeverityVariant(diagnosis.severity)}>
                      {diagnosis.severity}
                    </Badge>
                    <Badge variant={getStatusVariant(diagnosis.status)}>
                      {diagnosis.status}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </TabsContent>

      <TabsContent value="procedures" className="space-y-4">
        <div className="flex items-center justify-between">
          <h3>Medical Procedures</h3>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add Procedure
          </Button>
        </div>
        
        <div className="space-y-3">
          {history.procedures.map((procedure) => (
            <Card key={procedure.id}>
              <CardContent className="p-4">
                <div className="flex items-start space-x-3">
                  <div className="p-2 bg-blue-100 rounded-full">
                    <Activity className="h-4 w-4 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h4 className="mb-1">{procedure.name}</h4>
                    <div className="text-sm text-muted-foreground space-y-1">
                      <p>Date: {procedure.date}</p>
                      <p>Facility: {procedure.facility}</p>
                      <p>Outcome: {procedure.outcome}</p>
                    </div>
                  </div>
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Report
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </TabsContent>

      <TabsContent value="tests" className="space-y-4">
        <div className="flex items-center justify-between">
          <h3>Laboratory Results</h3>
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Add Result
          </Button>
        </div>
        
        <div className="space-y-3">
          {history.tests.map((test) => (
            <Card key={test.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 bg-green-100 rounded-full">
                      <FileText className="h-4 w-4 text-green-600" />
                    </div>
                    <div>
                      <h4 className="mb-1">{test.name}</h4>
                      <div className="text-sm text-muted-foreground space-y-1">
                        <p>Date: {test.date}</p>
                        <p>Result: {test.result}</p>
                        {test.notes && <p>Notes: {test.notes}</p>}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={getStatusVariant(test.status)}>
                      {test.status}
                    </Badge>
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      View
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </TabsContent>

      <TabsContent value="longitudinal" className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3>Longitudinal Follow-up Data</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Patient care trajectory with clinical outcomes and interventions
            </p>
          </div>
        </div>
        
        <div className="space-y-3">
          {history.longitudinalData.map((visit) => (
            <Card key={visit.id}>
              <CardContent className="p-4">
                <div className="flex items-start space-x-3">
                  <div className="p-2 bg-blue-100 rounded-full">
                    <Calendar className="h-4 w-4 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <h4>{visit.visitType}</h4>
                        <Badge variant={visit.followUpStatus === 'completed' ? 'default' : 
                                     visit.followUpStatus === 'overdue' ? 'destructive' : 'outline'}>
                          {visit.followUpStatus}
                        </Badge>
                      </div>
                      <span className="text-sm text-muted-foreground">{visit.date}</span>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="font-medium text-muted-foreground">Primary Outcome</p>
                        <p className="mt-1">{visit.primaryOutcome}</p>
                      </div>
                      
                      <div>
                        <p className="font-medium text-muted-foreground">Provider</p>
                        <p className="mt-1">{visit.provider}</p>
                      </div>
                      
                      <div className="md:col-span-2">
                        <p className="font-medium text-muted-foreground">Clinical Assessment</p>
                        <p className="mt-1">{visit.clinicalAssessment}</p>
                      </div>
                      
                      {visit.interventions && visit.interventions.length > 0 && (
                        <div>
                          <p className="font-medium text-muted-foreground">Interventions</p>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {visit.interventions.map((intervention, index) => (
                              <Badge key={index} variant="secondary" className="text-xs">
                                {intervention}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {visit.proteinBiomarkerChanges && (
                        <div>
                          <p className="font-medium text-muted-foreground">Protein Biomarker Changes</p>
                          <p className="mt-1 text-xs bg-green-50 p-2 rounded">{visit.proteinBiomarkerChanges}</p>
                        </div>
                      )}
                      
                      {visit.functionalStatus && (
                        <div>
                          <p className="font-medium text-muted-foreground">Functional Status</p>
                          <p className="mt-1">{visit.functionalStatus}</p>
                        </div>
                      )}
                      
                      {visit.nextFollowUp && (
                        <div>
                          <p className="font-medium text-muted-foreground">Next Follow-up</p>
                          <p className="mt-1 text-blue-600">{visit.nextFollowUp}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </TabsContent>
    </Tabs>
  );
}