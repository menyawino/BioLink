import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Progress } from "./ui/progress";
import { Zap, Activity, Eye, Download, Calendar, MapPin, Target } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';

interface MolecularImagingProps {
  imagingData: {
    petScans: Array<{
      id: string;
      date: string;
      tracer: string;
      indication: string;
      findings: string;
      suv: number;
      region: string;
      interpretation: 'normal' | 'abnormal' | 'indeterminate';
      images: string[];
    }>;
    spect: Array<{
      id: string;
      date: string;
      tracer: string;
      protocol: string;
      findings: string;
      perfusion: {
        rest: number;
        stress: number;
        reversibility: boolean;
      };
      segments: Array<{
        name: string;
        restScore: number;
        stressScore: number;
      }>;
    }>;
    molecularMRI: Array<{
      id: string;
      date: string;
      contrast: string;
      sequence: string;
      findings: string;
      enhancement: 'none' | 'mild' | 'moderate' | 'marked';
      measurements: {
        area: number;
        volume: number;
        signal: number;
      };
    }>;
    proteinBiomarkerImaging: Array<{
      id: string;
      date: string;
      technique: string;
      target: string;
      quantification: number;
      units: string;
      reference: string;
      interpretation: string;
    }>;
  };
}

export function MolecularImaging({ imagingData }: MolecularImagingProps) {
  const getInterpretationVariant = (interpretation: string) => {
    switch (interpretation) {
      case 'normal': return 'secondary';
      case 'abnormal': return 'destructive';
      case 'indeterminate': return 'default';
      default: return 'outline';
    }
  };

  const getEnhancementVariant = (enhancement: string) => {
    switch (enhancement) {
      case 'none': return 'secondary';
      case 'mild': return 'default';
      case 'moderate': return 'default';
      case 'marked': return 'destructive';
      default: return 'outline';
    }
  };

  const generateSegmentData = (segments: any[]) => {
    return segments.map(segment => ({
      ...segment,
      difference: segment.stressScore - segment.restScore
    }));
  };

  return (
    <Tabs defaultValue="pet" className="space-y-4">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger value="pet">PET Imaging</TabsTrigger>
        <TabsTrigger value="spect">SPECT</TabsTrigger>
        <TabsTrigger value="mri">Molecular MRI</TabsTrigger>
        <TabsTrigger value="proteinBiomarkers">Protein Biomarker Imaging</TabsTrigger>
      </TabsList>

      <TabsContent value="pet" className="space-y-4">
        <div className="flex items-center justify-between">
          <h3>PET Scan Results</h3>
          <Button size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Schedule Scan
          </Button>
        </div>
        
        <div className="space-y-4">
          {imagingData.petScans.map((scan) => (
            <Card key={scan.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 bg-blue-100 rounded-full">
                      <Zap className="h-4 w-4 text-blue-600" />
                    </div>
                    <div>
                      <h4 className="mb-1">PET Scan - {scan.tracer}</h4>
                      <div className="text-sm text-muted-foreground space-y-1">
                        <p>Date: {scan.date}</p>
                        <p>Indication: {scan.indication}</p>
                        <p>Region: {scan.region}</p>
                      </div>
                    </div>
                  </div>
                  <Badge variant={getInterpretationVariant(scan.interpretation)}>
                    {scan.interpretation}
                  </Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm">SUV Max</span>
                      <span className="">{scan.suv}</span>
                    </div>
                    <Progress value={(scan.suv / 10) * 100} className="h-2" />
                    <p className="text-xs text-muted-foreground mt-1">
                      Reference: &lt;2.5 normal
                    </p>
                  </div>
                  
                  <div className="flex space-x-2">
                    <Button variant="outline" size="sm">
                      <Eye className="h-4 w-4 mr-2" />
                      View Images
                    </Button>
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      Report
                    </Button>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h5 className="mb-2">Findings</h5>
                  <p className="text-sm text-muted-foreground">{scan.findings}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </TabsContent>

      <TabsContent value="spect" className="space-y-4">
        <div className="flex items-center justify-between">
          <h3>SPECT Myocardial Perfusion</h3>
          <Button size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Schedule SPECT
          </Button>
        </div>
        
        <div className="space-y-4">
          {imagingData.spect.map((scan) => (
            <Card key={scan.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 bg-red-100 rounded-full">
                      <Activity className="h-4 w-4 text-red-600" />
                    </div>
                    <div>
                      <h4 className="mb-1">SPECT - {scan.tracer}</h4>
                      <div className="text-sm text-muted-foreground space-y-1">
                        <p>Date: {scan.date}</p>
                        <p>Protocol: {scan.protocol}</p>
                      </div>
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    <Badge variant={scan.perfusion.reversibility ? 'destructive' : 'secondary'}>
                      {scan.perfusion.reversibility ? 'Reversible Defect' : 'No Defect'}
                    </Badge>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <h5 className="mb-3">Perfusion Summary</h5>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>Rest Perfusion</span>
                        <span>{scan.perfusion.rest}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Stress Perfusion</span>
                        <span>{scan.perfusion.stress}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Reserve</span>
                        <span>{(scan.perfusion.stress - scan.perfusion.rest).toFixed(1)}%</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={generateSegmentData(scan.segments)}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="restScore" fill="#3b82f6" name="Rest" />
                        <Bar dataKey="stressScore" fill="#ef4444" name="Stress" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h5 className="mb-2">Clinical Findings</h5>
                  <p className="text-sm text-muted-foreground">{scan.findings}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </TabsContent>

      <TabsContent value="mri" className="space-y-4">
        <div className="flex items-center justify-between">
          <h3>Molecular MRI Studies</h3>
          <Button size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Schedule MRI
          </Button>
        </div>
        
        <div className="space-y-4">
          {imagingData.molecularMRI.map((mri) => (
            <Card key={mri.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 bg-purple-100 rounded-full">
                      <MapPin className="h-4 w-4 text-purple-600" />
                    </div>
                    <div>
                      <h4 className="mb-1">Molecular MRI</h4>
                      <div className="text-sm text-muted-foreground space-y-1">
                        <p>Date: {mri.date}</p>
                        <p>Contrast: {mri.contrast}</p>
                        <p>Sequence: {mri.sequence}</p>
                      </div>
                    </div>
                  </div>
                  <Badge variant={getEnhancementVariant(mri.enhancement)}>
                    {mri.enhancement} enhancement
                  </Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-2xl mb-1">{mri.measurements.area}</div>
                    <p className="text-sm text-muted-foreground">Area (cm²)</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl mb-1">{mri.measurements.volume}</div>
                    <p className="text-sm text-muted-foreground">Volume (mL)</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl mb-1">{mri.measurements.signal}</div>
                    <p className="text-sm text-muted-foreground">Signal Intensity</p>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h5 className="mb-2">Imaging Findings</h5>
                  <p className="text-sm text-muted-foreground">{mri.findings}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </TabsContent>

      <TabsContent value="proteinBiomarkers" className="space-y-4">
        <div className="flex items-center justify-between">
          <h3>Molecular Protein Biomarker Imaging</h3>
          <Button size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Schedule Study
          </Button>
        </div>
        
        <div className="space-y-4">
          {imagingData.proteinBiomarkerImaging.map((proteinBiomarker) => (
            <Card key={proteinBiomarker.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 bg-purple-100 rounded-full">
                      <Target className="h-4 w-4 text-purple-600" />
                    </div>
                    <div>
                      <h4 className="mb-1">{proteinBiomarker.technique}</h4>
                      <div className="text-sm text-muted-foreground space-y-1">
                        <p>Date: {proteinBiomarker.date}</p>
                        <p>Target: {proteinBiomarker.target}</p>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg">{proteinBiomarker.quantification} {proteinBiomarker.units}</div>
                    <p className="text-sm text-muted-foreground">Reference: {proteinBiomarker.reference}</p>
                  </div>
                </div>
                
                <div className="border-t pt-4">
                  <h5 className="mb-2">Interpretation</h5>
                  <p className="text-sm text-muted-foreground">{proteinBiomarker.interpretation}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-4">
            <div className="flex items-start space-x-3">
              <Zap className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="text-blue-800">Molecular Imaging Applications</h4>
                <p className="text-sm text-blue-700 mt-1">
                  Molecular imaging allows visualization of biological processes at the cellular and molecular level. 
                  These techniques provide insights into metabolism, perfusion, inflammation, and molecular targets 
                  that conventional imaging cannot detect.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}