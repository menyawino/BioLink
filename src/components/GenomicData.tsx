import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Dna, AlertTriangle, TrendingUp, Pill, Shield, Info } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

interface GenomicDataProps {
  genomicData: {
    polygenic: {
      coronaryArteryDisease: number;
      myocardialInfarction: number;
      strokeRisk: number;
      atrialFibrillation: number;
    };
    variants: Array<{
      gene: string;
      variant: string;
      genotype: string;
      clinicalSignificance: 'pathogenic' | 'likely_pathogenic' | 'uncertain' | 'likely_benign' | 'benign';
      condition: string;
      frequency: number;
    }>;
    pharmacogenomics: Array<{
      drug: string;
      gene: string;
      genotype: string;
      metabolizer: 'poor' | 'intermediate' | 'normal' | 'rapid' | 'ultra-rapid';
      recommendation: string;
      confidence: 'high' | 'moderate' | 'low';
    }>;
    ancestry: {
      european: number;
      african: number;
      asian: number;
      native_american: number;
      other: number;
    };
  };
}

export function GenomicData({ genomicData }: GenomicDataProps) {
  const getSignificanceVariant = (significance: string) => {
    switch (significance) {
      case 'pathogenic': return 'destructive';
      case 'likely_pathogenic': return 'default';
      case 'uncertain': return 'outline';
      case 'likely_benign': return 'secondary';
      case 'benign': return 'secondary';
      default: return 'outline';
    }
  };

  const getMetabolizerVariant = (metabolizer: string) => {
    switch (metabolizer) {
      case 'poor': return 'destructive';
      case 'intermediate': return 'default';
      case 'normal': return 'secondary';
      case 'rapid': return 'default';
      case 'ultra-rapid': return 'destructive';
      default: return 'outline';
    }
  };

  const getRiskLevel = (score: number) => {
    if (score >= 0.8) return { level: 'High', variant: 'destructive', color: '#ef4444' };
    if (score >= 0.6) return { level: 'Moderate-High', variant: 'default', color: '#f97316' };
    if (score >= 0.4) return { level: 'Moderate', variant: 'outline', color: '#eab308' };
    if (score >= 0.2) return { level: 'Low-Moderate', variant: 'secondary', color: '#22c55e' };
    return { level: 'Low', variant: 'secondary', color: '#22c55e' };
  };

  const polygenicData = [
    { name: 'CAD', value: genomicData.polygenic.coronaryArteryDisease, fullName: 'Coronary Artery Disease' },
    { name: 'MI', value: genomicData.polygenic.myocardialInfarction, fullName: 'Myocardial Infarction' },
    { name: 'Stroke', value: genomicData.polygenic.strokeRisk, fullName: 'Stroke Risk' },
    { name: 'AFib', value: genomicData.polygenic.atrialFibrillation, fullName: 'Atrial Fibrillation' }
  ];

  const ancestryData = [
    { name: 'European', value: genomicData.ancestry.european, color: '#3b82f6' },
    { name: 'African', value: genomicData.ancestry.african, color: '#ef4444' },
    { name: 'Asian', value: genomicData.ancestry.asian, color: '#22c55e' },
    { name: 'Native American', value: genomicData.ancestry.native_american, color: '#f97316' },
    { name: 'Other', value: genomicData.ancestry.other, color: '#8b5cf6' }
  ].filter(item => item.value > 0);

  return (
    <Tabs defaultValue="polygenic" className="space-y-4">
      <TabsList className="grid w-full grid-cols-4">
        <TabsTrigger value="polygenic">Polygenic Risk</TabsTrigger>
        <TabsTrigger value="variants">Genetic Variants</TabsTrigger>
        <TabsTrigger value="pharmacogenomics">Drug Response</TabsTrigger>
        <TabsTrigger value="ancestry">Ancestry</TabsTrigger>
      </TabsList>

      <TabsContent value="polygenic" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-blue-500" />
              <span>Polygenic Risk Scores</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                {polygenicData.map((item) => {
                  const risk = getRiskLevel(item.value);
                  return (
                    <div key={item.name} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span>{item.fullName}</span>
                        <Badge variant={risk.variant as any}>
                          {risk.level}
                        </Badge>
                      </div>
                      <Progress value={item.value * 100} className="h-2" />
                      <p className="text-sm text-muted-foreground">
                        Percentile: {Math.round(item.value * 100)}th
                      </p>
                    </div>
                  );
                })}
              </div>
              
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={polygenicData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis domain={[0, 1]} />
                    <Tooltip 
                      formatter={(value: number, name, props) => [
                        `${Math.round(value * 100)}th percentile`, 
                        props.payload.fullName
                      ]}
                    />
                    <Bar dataKey="value" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-4">
            <div className="flex items-start space-x-3">
              <Info className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="text-blue-800">Polygenic Risk Score Interpretation</h4>
                <p className="text-sm text-blue-700 mt-1">
                  These scores represent genetic predisposition compared to the general population. 
                  High scores indicate increased genetic risk but do not guarantee disease development. 
                  Environmental factors and lifestyle significantly influence actual risk.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="variants" className="space-y-4">
        <div className="flex items-center justify-between">
          <h3>Clinically Relevant Variants</h3>
          <Badge variant="outline">{genomicData.variants.length} variants</Badge>
        </div>
        
        <div className="space-y-3">
          {genomicData.variants.map((variant, index) => (
            <Card key={index}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 bg-purple-100 rounded-full">
                      <Dna className="h-4 w-4 text-purple-600" />
                    </div>
                    <div>
                      <h4 className="mb-1">{variant.gene} - {variant.variant}</h4>
                      <div className="text-sm text-muted-foreground space-y-1">
                        <p>Genotype: {variant.genotype}</p>
                        <p>Condition: {variant.condition}</p>
                        <p>Population frequency: {(variant.frequency * 100).toFixed(2)}%</p>
                      </div>
                    </div>
                  </div>
                  <Badge variant={getSignificanceVariant(variant.clinicalSignificance)}>
                    {variant.clinicalSignificance.replace('_', ' ')}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </TabsContent>

      <TabsContent value="pharmacogenomics" className="space-y-4">
        <div className="flex items-center justify-between">
          <h3>Drug Response Genetics</h3>
          <Badge variant="outline">{genomicData.pharmacogenomics.length} medications</Badge>
        </div>
        
        <div className="space-y-3">
          {genomicData.pharmacogenomics.map((pgx, index) => (
            <Card key={index}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 bg-green-100 rounded-full">
                      <Pill className="h-4 w-4 text-green-600" />
                    </div>
                    <div className="flex-1">
                      <h4 className="mb-1">{pgx.drug}</h4>
                      <div className="text-sm text-muted-foreground space-y-1">
                        <p>Gene: {pgx.gene} | Genotype: {pgx.genotype}</p>
                        <p className="mt-2">{pgx.recommendation}</p>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col items-end space-y-2">
                    <Badge variant={getMetabolizerVariant(pgx.metabolizer)}>
                      {pgx.metabolizer} metabolizer
                    </Badge>
                    <Badge variant={pgx.confidence === 'high' ? 'secondary' : 'outline'}>
                      {pgx.confidence} confidence
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="p-4">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5" />
              <div>
                <h4 className="text-orange-800">Pharmacogenomic Considerations</h4>
                <p className="text-sm text-orange-700 mt-1">
                  Always consult with healthcare providers before making medication changes based on genetic results. 
                  These recommendations should be considered alongside clinical factors and drug interactions.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="ancestry" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Shield className="h-5 w-5 text-green-500" />
              <span>Genetic Ancestry</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={ancestryData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${(value * 100).toFixed(1)}%`}
                    >
                      {ancestryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => `${(value * 100).toFixed(1)}%`} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              
              <div className="space-y-3">
                {ancestryData.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div 
                        className="w-4 h-4 rounded-full" 
                        style={{ backgroundColor: item.color }}
                      />
                      <span>{item.name}</span>
                    </div>
                    <span>{(item.value * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-green-200 bg-green-50">
          <CardContent className="p-4">
            <div className="flex items-start space-x-3">
              <Info className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <h4 className="text-green-800">Ancestry & Medical Relevance</h4>
                <p className="text-sm text-green-700 mt-1">
                  Genetic ancestry information helps contextualize disease risk and drug response variants. 
                  Different populations have varying frequencies of medically relevant genetic variants.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}