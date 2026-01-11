import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Progress } from "./ui/progress";
import { TrendingUp, TrendingDown, Minus, Heart, Flame, Droplets, Activity, Calendar, Zap, Eye } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, ScatterChart, Scatter } from 'recharts';

interface ProteinBiomarkersProps {
  proteinBiomarkers: {
    cardiac: Array<{
      name: string;
      value: number;
      units: string;
      referenceRange: string;
      status: 'normal' | 'elevated' | 'high' | 'critical';
      trend: 'up' | 'down' | 'stable';
      lastUpdated: string;
      history: Array<{ date: string; value: number }>;
    }>;
    inflammatory: Array<{
      name: string;
      value: number;
      units: string;
      referenceRange: string;
      status: 'normal' | 'elevated' | 'high';
      trend: 'up' | 'down' | 'stable';
      lastUpdated: string;
      history: Array<{ date: string; value: number }>;
    }>;
    metabolic: Array<{
      name: string;
      value: number;
      units: string;
      referenceRange: string;
      status: 'normal' | 'abnormal' | 'borderline';
      trend: 'up' | 'down' | 'stable';
      lastUpdated: string;
      history: Array<{ date: string; value: number }>;
    }>;
    novel: Array<{
      name: string;
      value: number;
      units: string;
      referenceRange: string;
      description: string;
      clinicalSignificance: string;
      status: 'normal' | 'elevated' | 'research';
      lastUpdated: string;
    }>;
    riskPanels: {
      cardiovascularRisk: number;
      inflammatoryBurden: number;
      metabolicSyndrome: number;
      thrombotic: number;
    };
  };
  molecularImaging?: {
    petScans: Array<{
      id: string;
      date: string;
      tracer: string;
      indication: string;
      findings: string;
      suv: number;
      region: string;
      interpretation: 'normal' | 'abnormal' | 'indeterminate';
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

export function ProteinBiomarkers({ proteinBiomarkers, molecularImaging }: ProteinBiomarkersProps) {
  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'normal': return 'secondary';
      case 'elevated': case 'borderline': return 'default';
      case 'high': case 'abnormal': return 'default';
      case 'critical': return 'destructive';
      case 'research': return 'outline';
      default: return 'secondary';
    }
  };

  const getInterpretationVariant = (interpretation: string) => {
    switch (interpretation) {
      case 'normal': return 'secondary';
      case 'abnormal': return 'destructive';
      case 'indeterminate': return 'default';
      default: return 'outline';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-4 w-4 text-red-500" />;
      case 'down': return <TrendingDown className="h-4 w-4 text-green-500" />;
      case 'stable': return <Minus className="h-4 w-4 text-gray-500" />;
      default: return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  const getRiskLevel = (score: number) => {
    if (score >= 80) return { level: 'Very High', color: '#dc2626', variant: 'destructive' };
    if (score >= 60) return { level: 'High', color: '#ea580c', variant: 'default' };
    if (score >= 40) return { level: 'Moderate', color: '#ca8a04', variant: 'outline' };
    return { level: 'Low', color: '#16a34a', variant: 'secondary' };
  };

  const riskPanelData = [
    { name: 'CV Risk', value: proteinBiomarkers.riskPanels.cardiovascularRisk, fullName: 'Cardiovascular Risk' },
    { name: 'Inflammation', value: proteinBiomarkers.riskPanels.inflammatoryBurden, fullName: 'Inflammatory Burden' },
    { name: 'Metabolic', value: proteinBiomarkers.riskPanels.metabolicSyndrome, fullName: 'Metabolic Syndrome' },
    { name: 'Thrombotic', value: proteinBiomarkers.riskPanels.thrombotic, fullName: 'Thrombotic Risk' }
  ];

  return (
    <div className="space-y-6">
      {/* Risk Panel Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-red-500" />
            <span>Protein Biomarker Risk Assessment</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              {riskPanelData.map((panel) => {
                const risk = getRiskLevel(panel.value);
                return (
                  <div key={panel.name} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span>{panel.fullName}</span>
                      <Badge variant={risk.variant as any}>
                        {risk.level}
                      </Badge>
                    </div>
                    <Progress value={panel.value} className="h-2" />
                    <p className="text-sm text-muted-foreground">
                      Score: {panel.value}/100
                    </p>
                  </div>
                );
              })}
            </div>
            
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={riskPanelData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip 
                    formatter={(value: number, name, props) => [
                      `${value}/100`, 
                      props.payload.fullName
                    ]}
                  />
                  <Bar dataKey="value" fill="#ef4444" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Protein Biomarkers */}
      <Tabs defaultValue="cardiac" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="cardiac">Cardiac</TabsTrigger>
          <TabsTrigger value="inflammatory">Inflammatory</TabsTrigger>
          <TabsTrigger value="metabolic">Metabolic</TabsTrigger>
          <TabsTrigger value="novel">Novel Markers</TabsTrigger>
          <TabsTrigger value="molecular">Molecular Imaging</TabsTrigger>
        </TabsList>

        <TabsContent value="cardiac" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3>Cardiac Protein Biomarkers</h3>
            <Button size="sm">
              <Calendar className="h-4 w-4 mr-2" />
              Order Tests
            </Button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {proteinBiomarkers.cardiac.map((marker, index) => (
              <Card key={index}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-start space-x-3">
                      <div className="p-2 bg-red-100 rounded-full">
                        <Heart className="h-4 w-4 text-red-600" />
                      </div>
                      <div>
                        <h4 className="mb-1">{marker.name}</h4>
                        <p className="text-sm text-muted-foreground">
                          Updated: {marker.lastUpdated}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center space-x-1 mb-1">
                        <span className="text-lg">{marker.value} {marker.units}</span>
                        {getTrendIcon(marker.trend)}
                      </div>
                      <Badge variant={getStatusVariant(marker.status)}>
                        {marker.status}
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="mb-3">
                    <p className="text-sm text-muted-foreground">
                      Reference: {marker.referenceRange}
                    </p>
                  </div>

                  {marker.history.length > 0 && (
                    <div className="h-24">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={marker.history}>
                          <Line 
                            type="monotone" 
                            dataKey="value" 
                            stroke="#ef4444" 
                            strokeWidth={2}
                            dot={false}
                          />
                          <Tooltip />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="inflammatory" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3>Inflammatory Markers</h3>
            <Button size="sm">
              <Calendar className="h-4 w-4 mr-2" />
              Order Panel
            </Button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {proteinBiomarkers.inflammatory.map((marker, index) => (
              <Card key={index}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-start space-x-3">
                      <div className="p-2 bg-orange-100 rounded-full">
                        <Flame className="h-4 w-4 text-orange-600" />
                      </div>
                      <div>
                        <h4 className="mb-1">{marker.name}</h4>
                        <p className="text-sm text-muted-foreground">
                          Updated: {marker.lastUpdated}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center space-x-1 mb-1">
                        <span className="text-lg">{marker.value} {marker.units}</span>
                        {getTrendIcon(marker.trend)}
                      </div>
                      <Badge variant={getStatusVariant(marker.status)}>
                        {marker.status}
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="mb-3">
                    <p className="text-sm text-muted-foreground">
                      Reference: {marker.referenceRange}
                    </p>
                  </div>

                  {marker.history.length > 0 && (
                    <div className="h-24">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={marker.history}>
                          <Line 
                            type="monotone" 
                            dataKey="value" 
                            stroke="#f97316" 
                            strokeWidth={2}
                            dot={false}
                          />
                          <Tooltip />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="metabolic" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3>Metabolic Markers</h3>
            <Button size="sm">
              <Calendar className="h-4 w-4 mr-2" />
              Order Panel
            </Button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {proteinBiomarkers.metabolic.map((marker, index) => (
              <Card key={index}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-start space-x-3">
                      <div className="p-2 bg-blue-100 rounded-full">
                        <Droplets className="h-4 w-4 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="mb-1">{marker.name}</h4>
                        <p className="text-sm text-muted-foreground">
                          Updated: {marker.lastUpdated}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center space-x-1 mb-1">
                        <span className="text-lg">{marker.value} {marker.units}</span>
                        {getTrendIcon(marker.trend)}
                      </div>
                      <Badge variant={getStatusVariant(marker.status)}>
                        {marker.status}
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="mb-3">
                    <p className="text-sm text-muted-foreground">
                      Reference: {marker.referenceRange}
                    </p>
                  </div>

                  {marker.history.length > 0 && (
                    <div className="h-24">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={marker.history}>
                          <Line 
                            type="monotone" 
                            dataKey="value" 
                            stroke="#3b82f6" 
                            strokeWidth={2}
                            dot={false}
                          />
                          <Tooltip />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="novel" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3>Novel & Research Protein Biomarkers</h3>
            <Button size="sm">
              <Calendar className="h-4 w-4 mr-2" />
              Research Studies
            </Button>
          </div>
          
          <div className="space-y-4">
            {proteinBiomarkers.novel.map((marker, index) => (
              <Card key={index}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start space-x-3">
                      <div className="p-2 bg-purple-100 rounded-full">
                        <Activity className="h-4 w-4 text-purple-600" />
                      </div>
                      <div className="flex-1">
                        <h4 className="mb-1">{marker.name}</h4>
                        <p className="text-sm text-muted-foreground mb-2">
                          {marker.description}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          Updated: {marker.lastUpdated}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg mb-1">{marker.value} {marker.units}</div>
                      <Badge variant={getStatusVariant(marker.status)}>
                        {marker.status}
                      </Badge>
                      <p className="text-xs text-muted-foreground mt-1">
                        Ref: {marker.referenceRange}
                      </p>
                    </div>
                  </div>
                  
                  <div className="border-t pt-4">
                    <h5 className="text-sm mb-2">Clinical Significance</h5>
                    <p className="text-sm text-muted-foreground">
                      {marker.clinicalSignificance}
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="molecular" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3>Molecular Imaging Protein Biomarkers</h3>
            <Button size="sm">
              <Calendar className="h-4 w-4 mr-2" />
              Schedule Study
            </Button>
          </div>
          
          {molecularImaging?.petScans && molecularImaging.petScans.length > 0 && (
            <div className="space-y-4">
              <h4>PET Imaging Protein Biomarkers</h4>
              {molecularImaging.petScans.map((scan) => (
                <Card key={scan.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-start space-x-3">
                        <div className="p-2 bg-blue-100 rounded-full">
                          <Zap className="h-4 w-4 text-blue-600" />
                        </div>
                        <div>
                          <h4 className="mb-1">PET - {scan.tracer}</h4>
                          <p className="text-sm text-muted-foreground">
                            Date: {scan.date}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            Region: {scan.region}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg mb-1">SUV: {scan.suv}</div>
                        <Badge variant={getInterpretationVariant(scan.interpretation)}>
                          {scan.interpretation}
                        </Badge>
                      </div>
                    </div>
                    
                    <div className="border-t pt-3">
                      <h5 className="text-sm mb-1">Findings</h5>
                      <p className="text-sm text-muted-foreground">{scan.findings}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
          
          {molecularImaging?.proteinBiomarkerImaging && molecularImaging.proteinBiomarkerImaging.length > 0 && (
            <div className="space-y-4 mt-6">
              <h4>Targeted Molecular Imaging</h4>
              {molecularImaging.proteinBiomarkerImaging.map((proteinBiomarker) => (
                <Card key={proteinBiomarker.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-start space-x-3">
                        <div className="p-2 bg-green-100 rounded-full">
                          <Eye className="h-4 w-4 text-green-600" />
                        </div>
                        <div>
                          <h4 className="mb-1">{proteinBiomarker.technique}</h4>
                          <p className="text-sm text-muted-foreground">
                            Date: {proteinBiomarker.date}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            Target: {proteinBiomarker.target}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg mb-1">{proteinBiomarker.quantification} {proteinBiomarker.units}</div>
                        <p className="text-xs text-muted-foreground">
                          Ref: {proteinBiomarker.reference}
                        </p>
                      </div>
                    </div>
                    
                    <div className="border-t pt-3">
                      <h5 className="text-sm mb-1">Interpretation</h5>
                      <p className="text-sm text-muted-foreground">{proteinBiomarker.interpretation}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
          
          {(!molecularImaging?.petScans?.length && !molecularImaging?.proteinBiomarkerImaging?.length) && (
            <Card>
              <CardContent className="p-6 text-center text-muted-foreground">
                <Zap className="h-8 w-8 mx-auto mb-3 opacity-50" />
                <p>No molecular imaging protein biomarker data available</p>
                <p className="text-sm mt-1">Schedule molecular imaging studies to track protein biomarker expression</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
