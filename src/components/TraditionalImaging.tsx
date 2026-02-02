import { useEffect, useMemo, useState } from "react";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Eye, Download, Calendar, Camera, Heart, Brain, Monitor, Activity } from "lucide-react";
import echoImage from "../assets/echo.jpg";
import mriImage from "../assets/mri.jpg";
import ctImage from "../assets/ct.png";
import ekgFileUrl from "../assets/ekg/S1123.ecg?url";

interface TraditionalImagingProps {
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
  };
}

export function TraditionalImaging({ imaging }: TraditionalImagingProps) {
  const [ekgSamples, setEkgSamples] = useState<number[] | null>(null);
  const [ekgError, setEkgError] = useState<string | null>(null);

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

  useEffect(() => {
    let cancelled = false;

    const loadEkg = async () => {
      try {
        const response = await fetch(ekgFileUrl);
        const buffer = await response.arrayBuffer();
        if (cancelled) return;

        const view = new DataView(buffer);
        const samples: number[] = [];
        for (let i = 0; i + 1 < view.byteLength; i += 2) {
          samples.push(view.getInt16(i, true));
        }

        if (samples.length === 0) {
          setEkgError("No ECG samples found.");
          return;
        }

        setEkgSamples(samples);
      } catch (error) {
        if (!cancelled) {
          setEkgError("Unable to load ECG data.");
        }
      }
    };

    loadEkg();

    return () => {
      cancelled = true;
    };
  }, []);

  const ekgPath = useMemo(() => {
    if (!ekgSamples || ekgSamples.length === 0) return "";

    const targetPoints = 1200;
    const step = Math.max(1, Math.floor(ekgSamples.length / targetPoints));
    const displaySamples = ekgSamples.filter((_, index) => index % step === 0);
    const min = Math.min(...displaySamples);
    const max = Math.max(...displaySamples);
    const range = max - min || 1;
    const width = 1000;
    const height = 240;
    const padding = 12;

    return displaySamples
      .map((value, index) => {
        const x = padding + (index / (displaySamples.length - 1)) * (width - padding * 2);
        const normalized = (value - min) / range;
        const y = height - padding - normalized * (height - padding * 2);
        return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
      })
      .join(" ");
  }, [ekgSamples]);

  return (
    <Tabs defaultValue="echo" className="space-y-4">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger value="echo">Echocardiography</TabsTrigger>
        <TabsTrigger value="mri">Cardiac MRI</TabsTrigger>
        <TabsTrigger value="ct">CT Imaging</TabsTrigger>
        <TabsTrigger value="ekg">EKG</TabsTrigger>
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
          {imaging.echo.length === 0 && (
            <Card>
              <CardContent className="p-6">
                <div className="flex items-start space-x-3 mb-4">
                  <div className="p-2 bg-blue-100 rounded-full">
                    <Heart className="h-4 w-4 text-blue-600" />
                  </div>
                  <div>
                    <h4 className="mb-1">Echocardiogram</h4>
                    <p className="text-sm text-muted-foreground">
                      No echo measurements recorded. Showing the latest reference image.
                    </p>
                  </div>
                </div>
                <img src={echoImage} alt="Echocardiogram" className="w-full rounded-lg border" />
              </CardContent>
            </Card>
          )}
          {imaging.echo.map((echo) => {
            const efStatus = getEFStatus(echo.measurements.ef);
            const echoImages = echo.images.length ? echo.images : [echoImage];
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

                  <div className="mt-4">
                    <h5 className="mb-2">Imaging Preview</h5>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {echoImages.map((image, index) => (
                        <div key={`${echo.id}-echo-${index}`} className="overflow-hidden rounded-lg border">
                          <img src={image} alt={`Echo ${index + 1}`} className="h-56 w-full object-cover" />
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
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
          {imaging.mri.length === 0 && (
            <Card>
              <CardContent className="p-6">
                <div className="flex items-start space-x-3 mb-4">
                  <div className="p-2 bg-purple-100 rounded-full">
                    <Brain className="h-4 w-4 text-purple-600" />
                  </div>
                  <div>
                    <h4 className="mb-1">Cardiac MRI</h4>
                    <p className="text-sm text-muted-foreground">
                      No MRI measurements recorded. Showing the latest reference image.
                    </p>
                  </div>
                </div>
                <img src={mriImage} alt="Cardiac MRI" className="w-full rounded-lg border" />
              </CardContent>
            </Card>
          )}
          {imaging.mri.map((mri) => {
            const mriImages = mri.images.length ? mri.images : [mriImage];
            return (
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

                <div className="mt-4">
                  <h5 className="mb-2">Imaging Preview</h5>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {mriImages.map((image, index) => (
                      <div key={`${mri.id}-mri-${index}`} className="overflow-hidden rounded-lg border">
                        <img src={image} alt={`MRI ${index + 1}`} className="h-56 w-full object-cover" />
                      </div>
                    ))}
                  </div>
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
          {imaging.ct.length === 0 && (
            <Card>
              <CardContent className="p-6">
                <div className="flex items-start space-x-3 mb-4">
                  <div className="p-2 bg-green-100 rounded-full">
                    <Monitor className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <h4 className="mb-1">CT Imaging</h4>
                    <p className="text-sm text-muted-foreground">
                      No CT measurements recorded. Showing the latest reference image.
                    </p>
                  </div>
                </div>
                <img src={ctImage} alt="CT Imaging" className="w-full rounded-lg border" />
              </CardContent>
            </Card>
          )}
          {imaging.ct.map((ct) => {
            const ctImages = ct.images.length ? ct.images : [ctImage];
            return (
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

                <div className="mt-4">
                  <h5 className="mb-2">Imaging Preview</h5>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {ctImages.map((image, index) => (
                      <div key={`${ct.id}-ct-${index}`} className="overflow-hidden rounded-lg border">
                        <img src={image} alt={`CT ${index + 1}`} className="h-56 w-full object-cover" />
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
          })}
        </div>
      </TabsContent>

      <TabsContent value="ekg" className="space-y-4">
        <div className="flex items-center justify-between">
          <h3>Electrocardiogram (EKG)</h3>
          <Button size="sm" variant="outline" asChild>
            <a href={ekgFileUrl} download>
              <Download className="h-4 w-4 mr-2" />
              Download ECG
            </a>
          </Button>
        </div>

        <Card>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-full">
                <Activity className="h-4 w-4 text-red-600" />
              </div>
              <div>
                <h4 className="mb-1">Resting ECG Trace</h4>
                <p className="text-sm text-muted-foreground">
                  ECG waveform generated from the latest uploaded trace.
                </p>
              </div>
            </div>

            {ekgError && (
              <div className="text-sm text-destructive">{ekgError}</div>
            )}

            {!ekgError && !ekgSamples && (
              <div className="text-sm text-muted-foreground">Loading ECG data...</div>
            )}

            {!ekgError && ekgSamples && (
              <div className="overflow-hidden rounded-lg border bg-white">
                <svg viewBox="0 0 1000 240" className="w-full h-64">
                  <defs>
                    <pattern id="ekg-grid" width="50" height="50" patternUnits="userSpaceOnUse">
                      <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#f1f5f9" strokeWidth="1" />
                    </pattern>
                  </defs>
                  <rect width="1000" height="240" fill="url(#ekg-grid)" />
                  <path d={ekgPath} fill="none" stroke="#ef4444" strokeWidth="1.5" />
                </svg>
              </div>
            )}
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}