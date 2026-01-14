import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, ScatterChart, Scatter, ComposedChart, Area, AreaChart } from 'recharts';
import { TrendingUp, Users, Database, Activity, Heart, Dna, TestTube, Map, Loader2 } from "lucide-react";
import { GeographicMapping } from "./GeographicMapping";
import { useRegistryStats, useDemographics, useDataCompleteness, useGeographicData } from "../hooks/useAnalytics";

// Colors for charts
const COLORS = ['#e9322b', '#efb01b', '#00a2dd', '#22c55e', '#8b5cf6', '#6b7280', '#ec4899', '#f97316'];

// Fallback mock data for sections not covered by API
const sampleCompletenessData = [
  { type: 'Blood', collected: 1247, processed: 1230, stored: 1195 },
  { type: 'Plasma', collected: 892, processed: 885, stored: 870 },
  { type: 'Serum', collected: 756, processed: 745, stored: 738 },
  { type: 'DNA', collected: 634, processed: 620, stored: 612 },
  { type: 'RNA', collected: 289, processed: 276, stored: 265 },
  { type: 'Tissue', collected: 145, processed: 142, stored: 138 }
];

const enrollmentTrendData = [
  { month: 'Jan 2024', enrolled: 45, cumulative: 1089 },
  { month: 'Feb 2024', enrolled: 52, cumulative: 1141 },
  { month: 'Mar 2024', enrolled: 48, cumulative: 1189 },
  { month: 'Apr 2024', enrolled: 38, cumulative: 1227 },
  { month: 'May 2024', enrolled: 41, cumulative: 1268 },
  { month: 'Jun 2024', enrolled: 35, cumulative: 1303 },
  { month: 'Jul 2024', enrolled: 29, cumulative: 1332 },
  { month: 'Aug 2024', enrolled: 33, cumulative: 1365 },
  { month: 'Sep 2024', enrolled: 42, cumulative: 1407 },
  { month: 'Oct 2024', enrolled: 37, cumulative: 1444 },
  { month: 'Nov 2024', enrolled: 28, cumulative: 1472 },
  { month: 'Dec 2024', enrolled: 15, cumulative: 1487 }
];

// UpSet-style intersection data
const intersectionData = [
  { combination: 'Genomics', count: 95, types: ['Genomics'] },
  { combination: 'Biomarkers', count: 78, types: ['Biomarkers'] },
  { combination: 'Imaging', count: 62, types: ['Imaging'] },
  { combination: 'G + B', count: 156, types: ['Genomics', 'Biomarkers'] },
  { combination: 'G + I', count: 134, types: ['Genomics', 'Imaging'] },
  { combination: 'B + I', count: 189, types: ['Biomarkers', 'Imaging'] },
  { combination: 'G + B + I', count: 623, types: ['Genomics', 'Biomarkers', 'Imaging'] }
];

export function RegistryAnalytics() {
  // Fetch real data from API
  const { data: stats, isLoading: statsLoading, error: statsError } = useRegistryStats();
  const { data: demographics, isLoading: demoLoading } = useDemographics();
  const { data: completeness, isLoading: compLoading } = useDataCompleteness();
  const { data: geoData, isLoading: geoLoading } = useGeographicData();

  // Transform demographics data for age-gender chart (use correct field names from API)
  const demographicsChartData = demographics?.ageGender?.map(item => ({
    ageGroup: item.age_group,
    male: item.male || 0,
    female: item.female || 0
  })) || [];

  // Transform nationality data for pie chart (use correct field name from API)
  const nationalityData = demographics?.nationality?.map((item, index) => ({
    name: item.nationality,
    value: item.count,
    color: COLORS[index % COLORS.length]
  })) || [];

  // Fallback nationality data if API returns empty
  const nationalityChartData = nationalityData.length > 0 ? nationalityData : [
    { name: 'Saudi', value: 892, color: COLORS[0] },
    { name: 'Egyptian', value: 156, color: COLORS[1] },
    { name: 'Yemeni', value: 89, color: COLORS[2] },
    { name: 'Syrian', value: 67, color: COLORS[3] },
    { name: 'Other', value: 43, color: COLORS[4] }
  ];

  // Calculate gender totals with fallback
  const maleCount = demographics?.ageGender?.reduce((sum, g) => sum + (g.male || 0), 0) || 685;
  const femaleCount = demographics?.ageGender?.reduce((sum, g) => sum + (g.female || 0), 0) || 562;
  
  const genderChartData = [
    { name: 'Male', value: maleCount, color: '#3b82f6' },
    { name: 'Female', value: femaleCount, color: '#ec4899' }
  ];

  // Transform completeness data (use correct field names from API)
  const dataAvailabilityData = completeness ? [
    { category: 'Demographics', availability: 100 },
    { category: 'Physical Exam', availability: completeness.byCategory?.physical_exam || 0 },
    { category: 'Lab Results', availability: completeness.byCategory?.lab_results || 0 },
    { category: 'Echo Data', availability: completeness.byCategory?.echo || 0 },
    { category: 'MRI Data', availability: completeness.byCategory?.mri || 0 },
    { category: 'ECG Data', availability: completeness.byCategory?.ecg || 0 }
  ] : [];

  // Use correct field names from API
  const totalPatients = stats?.totalPatients || 0;
  const avgCompleteness = parseFloat(stats?.dataCompleteness || '0');
  const patientsWithEcho = stats?.withEcho || 0;
  const patientsWithMri = stats?.withMri || 0;

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Patients</p>
                {statsLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin mt-2" />
                ) : (
                  <p className="text-3xl">{totalPatients.toLocaleString()}</p>
                )}
              </div>
              <Users className="h-8 w-8" style={{ color: '#00a2dd' }} />
            </div>
            <div className="mt-2 flex items-center text-sm">
              <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              <span className="text-green-600">EHVol Registry</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Patients with Echo</p>
                {statsLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin mt-2" />
                ) : (
                  <p className="text-3xl">{patientsWithEcho}</p>
                )}
              </div>
              <Activity className="h-8 w-8" style={{ color: '#efb01b' }} />
            </div>
            <div className="mt-2 flex items-center text-sm">
              <Badge variant="secondary" className="text-xs">
                {totalPatients > 0 ? Math.round((patientsWithEcho / totalPatients) * 100) : 0}% coverage
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Patients with MRI</p>
                {statsLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin mt-2" />
                ) : (
                  <p className="text-3xl">{patientsWithMri}</p>
                )}
              </div>
              <Heart className="h-8 w-8" style={{ color: '#e9322b' }} />
            </div>
            <div className="mt-2 flex items-center text-sm">
              <Badge variant="secondary" className="text-xs">
                {totalPatients > 0 ? Math.round((patientsWithMri / totalPatients) * 100) : 0}% coverage
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg Data Completeness</p>
                {statsLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin mt-2" />
                ) : (
                  <p className="text-3xl">{Math.round(avgCompleteness)}%</p>
                )}
              </div>
              <Database className="h-8 w-8" style={{ color: '#00a2dd' }} />
            </div>
            <div className="mt-2 flex items-center text-sm">
              <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              <span className="text-green-600">High quality data</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="demographics" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="demographics">Demographics</TabsTrigger>
          <TabsTrigger value="samples">Sample Analysis</TabsTrigger>
          <TabsTrigger value="intersections">Data Intersections</TabsTrigger>
          <TabsTrigger value="completeness">Data Quality</TabsTrigger>
          <TabsTrigger value="trends">Enrollment Trends</TabsTrigger>
          <TabsTrigger value="geography">
            <Map className="h-4 w-4 mr-1" />
            Geographic Mapping
          </TabsTrigger>
        </TabsList>

        <TabsContent value="demographics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Gender Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                {demoLoading ? (
                  <div className="flex items-center justify-center h-[300px]">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={genderChartData}
                        cx="50%"
                        cy="50%"
                        outerRadius={100}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value}`}
                        isAnimationActive={true}
                        animationBegin={0}
                        animationDuration={800}
                        animationEasing="ease-out"
                      >
                        <Cell fill="#3b82f6" />
                        <Cell fill="#ec4899" />
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Nationality Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                {demoLoading ? (
                  <div className="flex items-center justify-center h-[300px]">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={nationalityChartData}
                        cx="50%"
                        cy="50%"
                        outerRadius={100}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value}`}
                        isAnimationActive={true}
                        animationBegin={0}
                        animationDuration={800}
                        animationEasing="ease-out"
                      >
                        {nationalityChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Age Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              {demoLoading ? (
                <div className="flex items-center justify-center h-[300px]">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={demographics?.ageGender || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="age_group" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="male" stackId="a" fill="#3b82f6" name="Male" />
                    <Bar dataKey="female" stackId="a" fill="#ec4899" name="Female" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="samples" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Sample Collection & Processing Pipeline</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={sampleCompletenessData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="type" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="collected" fill="#3b82f6" name="Collected" />
                  <Bar dataKey="processed" fill="#22c55e" name="Processed" />
                  <Bar dataKey="stored" fill="#8b5cf6" name="Stored" />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="intersections" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Data Type Intersections (UpSet-style)</CardTitle>
              <p className="text-sm text-muted-foreground">
                Shows how different data types overlap across patients. G=Genomics, B=Biomarkers, I=Imaging
              </p>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={intersectionData} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="combination" type="category" width={80} />
                  <Tooltip 
                    formatter={(value, name, props) => [
                      `${value} patients`,
                      `Data Types: ${props.payload.types.join(', ')}`
                    ]}
                  />
                  <Bar dataKey="count" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
              
              <div className="grid grid-cols-3 gap-4 mt-6">
                <div className="text-center">
                  <div className="flex items-center justify-center mb-2">
                    <Dna className="h-6 w-6 text-blue-500" />
                  </div>
                  <p className="text-sm">Genomics Data</p>
                  <p className="text-2xl">1,108</p>
                  <p className="text-xs text-muted-foreground">74% of patients</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center mb-2">
                    <TestTube className="h-6 w-6 text-green-500" />
                  </div>
                  <p className="text-sm">Protein Biomarker Data</p>
                  <p className="text-2xl">1,156</p>
                </div>
                <div className="text-center">
                  <div className="flex items-center justify-center mb-2">
                    <Heart className="h-6 w-6 text-red-500" />
                  </div>
                  <p className="text-sm">Imaging Data</p>
                  <p className="text-2xl">1,298</p>
                  <p className="text-xs text-muted-foreground">87% of patients</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="completeness" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Data Availability by Category</CardTitle>
            </CardHeader>
            <CardContent>
              {compLoading ? (
                <div className="flex items-center justify-center h-[300px]">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : (
                <>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={dataAvailabilityData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="category" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip formatter={(value) => [`${value}%`, 'Availability']} />
                      <Bar 
                        dataKey="availability" 
                        fill="#22c55e"
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                  
                  <div className="mt-4 space-y-2">
                    {dataAvailabilityData.map((item) => (
                      <div key={item.category} className="flex items-center justify-between text-sm">
                        <span>{item.category}</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${
                                item.availability >= 80 ? 'bg-green-500' :
                                item.availability >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${item.availability}%` }}
                            />
                          </div>
                          <span className="w-12 text-right">{Math.round(item.availability)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Patient Enrollment Trends</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <ComposedChart data={enrollmentTrendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Bar yAxisId="left" dataKey="enrolled" fill="#3b82f6" name="Monthly Enrollment" />
                  <Line 
                    yAxisId="right" 
                    type="monotone" 
                    dataKey="cumulative" 
                    stroke="#ef4444" 
                    strokeWidth={3}
                    name="Cumulative Total"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="geography" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Geographic Mapping</CardTitle>
            </CardHeader>
            <CardContent>
              <GeographicMapping />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}