import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import { Eye, Download, Calendar, Camera, Heart, Brain, Zap, Monitor } from "lucide-react";

interface ImagingDataProps {
  imaging: {
    ct: Array<{
      id: string;
      date: string;
      type: string;
      contrast: boolean;
      indication: string;
      findings: string;
      measurements: {
        calciumScore?: number;
        stenosis?: string;
        dimensions?: string;
      };
      radiologist: string;
      priority: 'routine' | 'urgent' | 'stat';
      images: string[];
    }>;
    mri: Array<{
      id: string;
      date: string;
      sequence: string;
      fieldStrength: string;
      indication: string;
      findings: string;
      measurements: {
        ejectionFraction?: number;
        wallThickness?: string;
        perfusion?: string;
      };
      radiologist: string;
      images: string[];
    }>;
    echo: Array<{
      id: string;
      date: string;
      type: string;
      indication: string;
      measurements: {
        ef: number;
        lv: string;
        rv: string;
        valves: string;
      };
      findings: string;
      cardiologist: string;
      images: string[];
    }>;
    nuclear: Array<{
      id: string;
      date: string;
      study: string;
      tracer: string;
      indication: string;
      findings: string;
      quantitative: {
        perfusion: number;
        viability: number;
        function: number;
      };
      physician: string;
      images: string[];
    }>;
  };
}

export function ImagingData({ imaging }: ImagingDataProps) {
  const getPriorityVariant = (priority: string) => {
    switch (priority) {
      case 'stat': return 'destructive';
      case 'urgent': return 'default';
      case 'routine': return 'secondary';
      default: return 'secondary';
    }
  };

  const getEFStatus = (ef: number) => {
    if (ef >= 55) return { status: 'Normal', variant: 'secondary' };
    if (ef >= 40) return { status: 'Mild Dysfunction', variant: 'default' };
    if (ef >= 30) return { status: 'Moderate Dysfunction', variant: 'default' };
    return { status: 'Severe Dysfunction', variant: 'destructive' };
  };

  return (
    <Tabs defaultValue="echo" className="space-y-4">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger value="echo">Echocardiography</TabsTrigger>
        <TabsTrigger value="ct">CT Scans</TabsTrigger>
        <TabsTrigger value="mri">Cardiac MRI</TabsTrigger>
        <TabsTrigger value="nuclear">Nuclear</TabsTrigger>
      </TabsList>

      <TabsContent value="echo" className="space-y-4">
        <div className="flex items-center justify-between">
          <h3>Echocardiographic Studies</h3>
          <Button size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Schedule Echo
          </Button>
        </div>
        
        <div className="space-y-4">
          {imaging.echo.map((echo) => {
            const efStatus = getEFStatus(echo.measurements.ef);
            return (
              <Card key={echo.id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start space-x-3">
                      <div className="p-2 bg-blue-100 rounded-full">
                        <Heart className="h-4 w-4 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="mb-1">{echo.type}</h4>
                        <div className="text-sm text-muted-foreground space-y-1">
                          <p>Date: {echo.date}</p>
                          <p>Indication: {echo.indication}</p>
                          <p>Cardiologist: {echo.cardiologist}</p>
                        </div>
                      </div>
                    </div>
                    <Badge variant={efStatus.variant as any}>
                      EF: {echo.measurements.ef}% - {efStatus.status}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <h5 className="mb-2">Key Measurements</h5>
                      <div className="text-sm space-y-1">
                        <div className="flex justify-between">
                          <span>Ejection Fraction:</span>
                          <span>{echo.measurements.ef}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>LV Function:</span>
                          <span>{echo.measurements.lv}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>RV Function:</span>
                          <span>{echo.measurements.rv}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Valves:</span>
                          <span>{echo.measurements.valves}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex flex-col space-y-2">
                      <Button variant="outline" size="sm">
                        <Eye className="h-4 w-4 mr-2" />
                        View Images ({echo.images.length})
                      </Button>
                      <Button variant="outline" size="sm">
                        <Download className="h-4 w-4 mr-2" />
                        Download Report
                      </Button>
                      <Button variant="outline" size="sm">
                        <Camera className="h-4 w-4 mr-2" />
                        DICOM Files
                      </Button>
                    </div>
                  </div>

                  <div className="border-t pt-4">
                    <h5 className="mb-2">Clinical Findings</h5>
                    <p className="text-sm text-muted-foreground">{echo.findings}</p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </TabsContent>

      <TabsContent value="ct" className="space-y-4">
        <div className="flex items-center justify-between">
          <h3>CT Imaging Studies</h3>
          <Button size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Schedule CT
          </Button>
        </div>
        
        <div className="space-y-4">
          {imaging.ct.map((ct) => (
            <Card key={ct.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 bg-green-100 rounded-full">
                      <Monitor className="h-4 w-4 text-green-600" />
                    </div>
                    <div>
                      <h4 className="mb-1">{ct.type}</h4>
                      <div className="text-sm text-muted-foreground space-y-1">
                        <p>Date: {ct.date}</p>
                        <p>Indication: {ct.indication}</p>
                        <p>Radiologist: {ct.radiologist}</p>
                        <p>Contrast: {ct.contrast ? 'Yes' : 'No'}</p>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col space-y-2">
                    <Badge variant={getPriorityVariant(ct.priority)}>
                      {ct.priority}
                    </Badge>
                    {ct.measurements.calciumScore && (
                      <Badge variant={ct.measurements.calciumScore > 100 ? 'destructive' : 'secondary'}>
                        Calcium: {ct.measurements.calciumScore}
                      </Badge>
                    )}
                  </div>
                </div>

                {ct.measurements.calciumScore && (
                  <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                    <div className="flex justify-between items-center">
                      <span>Coronary Calcium Score:</span>
                      <span className="">{ct.measurements.calciumScore}</span>
                    </div>
                    <div className="text-sm text-muted-foreground mt-1">
                      {ct.measurements.stenosis && `Stenosis: ${ct.measurements.stenosis}`}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    {ct.measurements.dimensions && (
                      <div>
                        <h5 className="mb-2">Measurements</h5>
                        <p className="text-sm text-muted-foreground">
                          {ct.measurements.dimensions}
                        </p>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex flex-col space-y-2">
                    <Button variant="outline" size="sm">
                      <Eye className="h-4 w-4 mr-2" />
                      View Images ({ct.images.length})
                    </Button>
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      Download Report
                    </Button>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h5 className="mb-2">Radiological Findings</h5>
                  <p className="text-sm text-muted-foreground">{ct.findings}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </TabsContent>

      <TabsContent value="mri" className="space-y-4">
        <div className="flex items-center justify-between">
          <h3>Cardiac MRI Studies</h3>
          <Button size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Schedule MRI
          </Button>
        </div>
        
        <div className="space-y-4">
          {imaging.mri.map((mri) => (
            <Card key={mri.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 bg-purple-100 rounded-full">
                      <Brain className="h-4 w-4 text-purple-600" />
                    </div>
                    <div>
                      <h4 className="mb-1">Cardiac MRI - {mri.sequence}</h4>
                      <div className="text-sm text-muted-foreground space-y-1">
                        <p>Date: {mri.date}</p>
                        <p>Field Strength: {mri.fieldStrength}</p>
                        <p>Indication: {mri.indication}</p>
                        <p>Radiologist: {mri.radiologist}</p>
                      </div>
                    </div>
                  </div>
                  {mri.measurements.ejectionFraction && (
                    <Badge variant={mri.measurements.ejectionFraction >= 55 ? 'secondary' : 'default'}>
                      EF: {mri.measurements.ejectionFraction}%
                    </Badge>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <h5 className="mb-2">MRI Measurements</h5>
                    <div className="text-sm space-y-1">
                      {mri.measurements.ejectionFraction && (
                        <div className="flex justify-between">
                          <span>Ejection Fraction:</span>
                          <span>{mri.measurements.ejectionFraction}%</span>
                        </div>
                      )}
                      {mri.measurements.wallThickness && (
                        <div className="flex justify-between">
                          <span>Wall Thickness:</span>
                          <span>{mri.measurements.wallThickness}</span>
                        </div>
                      )}
                      {mri.measurements.perfusion && (
                        <div className="flex justify-between">
                          <span>Perfusion:</span>
                          <span>{mri.measurements.perfusion}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex flex-col space-y-2">
                    <Button variant="outline" size="sm">
                      <Eye className="h-4 w-4 mr-2" />
                      View Images ({mri.images.length})
                    </Button>
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      Download Report
                    </Button>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h5 className="mb-2">MRI Findings</h5>
                  <p className="text-sm text-muted-foreground">{mri.findings}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </TabsContent>

      <TabsContent value="nuclear" className="space-y-4">
        <div className="flex items-center justify-between">
          <h3>Nuclear Cardiology</h3>
          <Button size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Schedule Study
          </Button>
        </div>
        
        <div className="space-y-4">
          {imaging.nuclear.map((nuclear) => (
            <Card key={nuclear.id}>
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 bg-orange-100 rounded-full">
                      <Zap className="h-4 w-4 text-orange-600" />
                    </div>
                    <div>
                      <h4 className="mb-1">{nuclear.study}</h4>
                      <div className="text-sm text-muted-foreground space-y-1">
                        <p>Date: {nuclear.date}</p>
                        <p>Tracer: {nuclear.tracer}</p>
                        <p>Indication: {nuclear.indication}</p>
                        <p>Physician: {nuclear.physician}</p>
                      </div>
                    </div>
                  </div>
                  <Badge variant={nuclear.quantitative.perfusion >= 80 ? 'secondary' : 'default'}>
                    Perfusion: {nuclear.quantitative.perfusion}%
                  </Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <h5 className="mb-2">Quantitative Results</h5>
                    <div className="text-sm space-y-1">
                      <div className="flex justify-between">
                        <span>Perfusion:</span>
                        <span>{nuclear.quantitative.perfusion}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Viability:</span>
                        <span>{nuclear.quantitative.viability}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Function:</span>
                        <span>{nuclear.quantitative.function}%</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex flex-col space-y-2">
                    <Button variant="outline" size="sm">
                      <Eye className="h-4 w-4 mr-2" />
                      View Images ({nuclear.images.length})
                    </Button>
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      Download Report
                    </Button>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h5 className="mb-2">Study Findings</h5>
                  <p className="text-sm text-muted-foreground">{nuclear.findings}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </TabsContent>
    </Tabs>
  );
}