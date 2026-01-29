import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, ScatterChart, Scatter, ComposedChart, Area, AreaChart } from 'recharts';
import { TrendingUp, Users, Database, Activity, Heart, Map, Loader2 } from "lucide-react";
import { GeographicMapping } from "./GeographicMapping";
import { DataNotAvailable } from "./DataNotAvailable";
import { useRegistryStats, useDemographics, useDataCompleteness, useComorbidities, useEnrollmentTrends } from "../hooks/useAnalytics";

// Colors for charts
const COLORS = ['#e9322b', '#efb01b', '#00a2dd', '#22c55e', '#8b5cf6', '#6b7280', '#ec4899', '#f97316'];

export function RegistryAnalytics() {
  // Fetch enrollment trends data
  const { data: enrollmentTrends, isLoading: enrollmentLoading } = useEnrollmentTrends();

  // Transform enrollment trends data for chart
  const enrollmentTrendData = enrollmentTrends ? enrollmentTrends.map((item: any) => ({
    month: item.month,
    enrolled: item.enrolled,
    cumulative: item.cumulative
  })) : undefined;

  // Fetch real data from API
  const { data: stats, isLoading: statsLoading, error: statsError } = useRegistryStats();
  const { data: demographics, isLoading: demoLoading } = useDemographics();
  const { data: completeness, isLoading: compLoading } = useDataCompleteness();
  const { data: comorbidities, isLoading: comorbidityLoading } = useComorbidities();

  // Transform demographics data for age-gender chart (use correct field names from API)
  const demographicsChartData = demographics?.ageGender?.map(item => ({
    ageGroup: item.age_group,
    male: item.male,
    female: item.female
  }));

  // Transform nationality data for pie chart (use correct field name from API)
  const nationalityChartData = demographics?.nationality?.map((item, index) => ({
    name: item.nationality,
    value: item.count,
    color: COLORS[index % COLORS.length]
  }));

  // Calculate gender totals
  const maleCount = demographics?.ageGender?.reduce((sum, g) => sum + (g.male || 0), 0);
  const femaleCount = demographics?.ageGender?.reduce((sum, g) => sum + (g.female || 0), 0);
  
  const genderChartData = maleCount !== undefined && femaleCount !== undefined ? [
    { name: 'Male', value: maleCount, color: '#3b82f6' },
    { name: 'Female', value: femaleCount, color: '#ec4899' }
  ] : undefined;

  // Transform completeness data (use correct field names from API)
  const dataAvailabilityData = completeness ? [
    { category: 'Overall', availability: completeness.byCategory?.overall },
    { category: 'Physical Exam', availability: completeness.byCategory?.physical_exam },
    { category: 'Lab Results', availability: completeness.byCategory?.lab_results },
    { category: 'Echo Data', availability: completeness.byCategory?.echo },
    { category: 'MRI Data', availability: completeness.byCategory?.mri },
    { category: 'ECG Data', availability: completeness.byCategory?.ecg }
  ].filter(item => typeof item.availability === 'number' && Number.isFinite(item.availability)) : undefined;

  // Transform data completeness for sample processing chart
  const realSampleCompletenessData = completeness && stats?.totalPatients ? [
    { type: 'Demographics', collected: stats.totalPatients, processed: stats.totalPatients, stored: stats.totalPatients },
    { type: 'Physical Exam', collected: Math.round((stats.totalPatients * (completeness.byCategory?.physical_exam || 0)) / 100), processed: Math.round((stats.totalPatients * (completeness.byCategory?.physical_exam || 0)) / 100), stored: Math.round((stats.totalPatients * (completeness.byCategory?.physical_exam || 0)) / 100) },
    { type: 'Lab Results', collected: Math.round((stats.totalPatients * (completeness.byCategory?.lab_results || 0)) / 100), processed: Math.round((stats.totalPatients * (completeness.byCategory?.lab_results || 0)) / 100), stored: Math.round((stats.totalPatients * (completeness.byCategory?.lab_results || 0)) / 100) },
    { type: 'Echo Data', collected: stats.withEcho, processed: stats.withEcho, stored: stats.withEcho },
    { type: 'MRI Data', collected: stats.withMri, processed: stats.withMri, stored: stats.withMri },
    { type: 'ECG Data', collected: stats.withEcg, processed: stats.withEcg, stored: stats.withEcg }
  ] : undefined;

  // Create real intersection data based on data availability
  const realIntersectionData = stats ? [
    { combination: 'Echo Only', count: (stats.withEcho || 0) - (stats.withBothEchoMri || 0), types: ['Echo'] },
    { combination: 'MRI Only', count: (stats.withMri || 0) - (stats.withBothEchoMri || 0), types: ['MRI'] },
    { combination: 'Echo + MRI', count: stats.withBothEchoMri || 0, types: ['Echo', 'MRI'] }
  ].filter(item => item.count > 0) : undefined;

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
                  <p className="text-3xl">{stats?.totalPatients?.toLocaleString() || '0'}</p>
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
                  <p className="text-3xl">{stats?.withEcho || 0}</p>
                )}
              </div>
              <Activity className="h-8 w-8" style={{ color: '#efb01b' }} />
            </div>
            <div className="mt-2 flex items-center text-sm">
              <Badge variant="secondary" className="text-xs">
                {stats?.totalPatients && stats?.totalPatients > 0 ? Math.round((stats.withEcho / stats.totalPatients) * 100) : 0}% coverage
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
                  <p className="text-3xl">{stats?.withMri || 0}</p>
                )}
              </div>
              <Heart className="h-8 w-8" style={{ color: '#e9322b' }} />
            </div>
            <div className="mt-2 flex items-center text-sm">
              <Badge variant="secondary" className="text-xs">
                {stats?.totalPatients && stats?.totalPatients > 0 ? Math.round((stats.withMri / stats.totalPatients) * 100) : 0}% coverage
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
                  <p className="text-3xl">{completeness ? Math.round(Object.values(completeness.byCategory || {}).reduce((a, b) => a + b, 0) / Object.keys(completeness.byCategory || {}).length) : 0}%</p>
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
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="demographics">Demographics</TabsTrigger>
          <TabsTrigger value="comorbidities">Comorbidities</TabsTrigger>
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
                ) : genderChartData ? (
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
                ) : (
                  <DataNotAvailable title="Gender Distribution" message="Gender distribution data is not available" />
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
                ) : nationalityChartData ? (
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
                ) : (
                  <DataNotAvailable title="Nationality Distribution" message="Nationality distribution data is not available" />
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
              ) : demographics?.ageGender ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={demographics.ageGender}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="age_group" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="male" stackId="a" fill="#3b82f6" name="Male" />
                    <Bar dataKey="female" stackId="a" fill="#ec4899" name="Female" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <DataNotAvailable title="Age Distribution" message="Age distribution data is not available" />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="comorbidities" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Comorbidity Prevalence</CardTitle>
              </CardHeader>
              <CardContent>
                {comorbidityLoading ? (
                  <div className="flex items-center justify-center h-[300px]">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : comorbidities?.conditions ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={Object.entries(comorbidities.conditions).map(([key, value]) => ({
                      condition: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                      count: value
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="condition" angle={-45} textAnchor="end" height={80} />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill="#e9322b" name="Patients" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <DataNotAvailable title="Comorbidity Prevalence" message="Comorbidity data is not available" />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Comorbidity Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                {comorbidityLoading ? (
                  <div className="flex items-center justify-center h-[300px]">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : comorbidities?.comorbidityDistribution ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={comorbidities.comorbidityDistribution.map(item => ({
                      comorbidities: `${item.comorbidity} conditions`,
                      patients: item.count
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="comorbidities" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="patients" fill="#efb01b" name="Patients" />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <DataNotAvailable title="Comorbidity Distribution" message="Comorbidity distribution data is not available" />
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="samples" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Sample Collection & Processing Pipeline</CardTitle>
            </CardHeader>
            <CardContent>
              {compLoading ? (
                <div className="flex items-center justify-center h-[300px]">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : realSampleCompletenessData ? (
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={realSampleCompletenessData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="type" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="collected" fill="#3b82f6" name="Collected" />
                    <Bar dataKey="processed" fill="#22c55e" name="Processed" />
                    <Bar dataKey="stored" fill="#8b5cf6" name="Stored" />
                  </ComposedChart>
                </ResponsiveContainer>
              ) : (
                <DataNotAvailable title="Sample Processing Status" message="Sample completeness data is not available" />
              )}
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
              {statsLoading ? (
                <div className="flex items-center justify-center h-[400px]">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : realIntersectionData ? (
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={realIntersectionData} layout="horizontal">
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
              ) : (
                <DataNotAvailable title="Data Type Intersections" message="Data intersection data is not available" />
              )}
              
              {stats ? (
                <div className="grid grid-cols-3 gap-4 mt-6">
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-2">
                      <Activity className="h-6 w-6 text-blue-500" />
                    </div>
                    <p className="text-sm">Echo Data</p>
                    <p className="text-2xl">{stats.withEcho || 0}</p>
                    <p className="text-xs text-muted-foreground">
                      {stats.totalPatients ? Math.round((stats.withEcho / stats.totalPatients) * 100) : 0}% of patients
                    </p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-2">
                      <Heart className="h-6 w-6 text-red-500" />
                    </div>
                    <p className="text-sm">MRI Data</p>
                    <p className="text-2xl">{stats.withMri || 0}</p>
                    <p className="text-xs text-muted-foreground">
                      {stats.totalPatients ? Math.round((stats.withMri / stats.totalPatients) * 100) : 0}% of patients
                    </p>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-2">
                      <Database className="h-6 w-6 text-green-500" />
                    </div>
                    <p className="text-sm">Echo + MRI</p>
                    <p className="text-2xl">{stats.withBothEchoMri || 0}</p>
                    <p className="text-xs text-muted-foreground">
                      {stats.totalPatients ? Math.round((stats.withBothEchoMri / stats.totalPatients) * 100) : 0}% of patients
                    </p>
                  </div>
                </div>
              ) : (
                <div className="mt-6">
                  <DataNotAvailable title="Intersection Summary" message="Intersection summary data is not available" />
                </div>
              )}
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
              ) : dataAvailabilityData && dataAvailabilityData.length > 0 ? (
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
              ) : (
                <DataNotAvailable title="Data Availability by Category" message="Data availability data is not available" />
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
              {enrollmentLoading ? (
                <div className="flex items-center justify-center h-[400px]">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : enrollmentTrendData ? (
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
              ) : (
                <DataNotAvailable title="Patient Enrollment Trends" message="Enrollment trends data is not available" />
              )}
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