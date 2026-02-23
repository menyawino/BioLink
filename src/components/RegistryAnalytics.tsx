import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Line, ComposedChart } from 'recharts';
import { TrendingUp, Users, Database, Activity, Heart, Map, Loader2 } from "lucide-react";
import { GeographicMapping } from "./GeographicMapping";
import { DataNotAvailable } from "./DataNotAvailable";
import { useRegistryStats, useDemographics, useDataCompleteness, useComorbidities, useEnrollmentTrends } from "../hooks/useAnalytics";
import type { DatasetFilter } from "../api/patients";

// Colors for charts
const COLORS = ['#e9322b', '#efb01b', '#00a2dd', '#22c55e', '#8b5cf6', '#6b7280', '#ec4899', '#f97316'];

export function RegistryAnalytics() {
  const [dataset, setDataset] = useState<DatasetFilter>("all");

  // Fetch enrollment trends data
  const { data: enrollmentTrends, isLoading: enrollmentLoading } = useEnrollmentTrends(dataset);

  // Transform enrollment trends data for chart (no client-side date cleanup)
  const enrollmentTrendData = enrollmentTrends ? enrollmentTrends.map((item: any) => ({
    month: item.month,
    enrolled: item.enrolled,
    cumulative: item.cumulative
  })) : undefined;

  // Fetch real data from API
  const { data: stats, isLoading: statsLoading, error: statsError } = useRegistryStats(dataset);
  const { data: ehvolStats, isLoading: ehvolStatsLoading } = useRegistryStats("ehvol");
  const { data: bhsStats, isLoading: bhsStatsLoading } = useRegistryStats("bhs");
  const { data: demographics, isLoading: demoLoading } = useDemographics(dataset);
  const { data: completeness, isLoading: compLoading } = useDataCompleteness(dataset);
  const { data: comorbidities, isLoading: comorbidityLoading } = useComorbidities(dataset);

  // Transform demographics data for age-gender chart (use correct field names from API)
  const demographicsChartData = demographics?.ageGender?.map(item => ({
    ageGroup: item.age_group,
    male: item.male,
    female: item.female
  }));

  // Transform nationality data and collapse minor segments into "Other"
  const nationalityChartData = demographics?.nationality
    ? (() => {
        const sorted = [...demographics.nationality].sort((a, b) => b.count - a.count);
        const top = sorted.slice(0, 6);
        const remainder = sorted.slice(6).reduce((sum, item) => sum + item.count, 0);
        const merged = remainder > 0
          ? [...top, { nationality: 'Other', count: remainder }]
          : top;
        return merged.map((item, index) => ({
          name: item.nationality,
          value: item.count,
          color: COLORS[index % COLORS.length]
        }));
      })()
    : undefined;

  // Calculate gender totals
  const maleCount = stats?.maleCount ?? demographics?.ageGender?.reduce((sum, g) => sum + (g.male || 0), 0);
  const femaleCount = stats?.femaleCount ?? demographics?.ageGender?.reduce((sum, g) => sum + (g.female || 0), 0);
  
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

  const latestTrend = enrollmentTrendData && enrollmentTrendData.length > 0
    ? enrollmentTrendData[enrollmentTrendData.length - 1]
    : undefined;
  const previousTrend = enrollmentTrendData && enrollmentTrendData.length > 1
    ? enrollmentTrendData[enrollmentTrendData.length - 2]
    : undefined;
  const momGrowth = latestTrend && previousTrend && previousTrend.enrolled > 0
    ? Math.round(((latestTrend.enrolled - previousTrend.enrolled) / previousTrend.enrolled) * 100)
    : 0;

  const conditions = comorbidities?.conditions;
  const conditionRates = conditions && stats?.totalPatients ? Object.entries(conditions)
    .map(([key, value]) => ({
      condition: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      rate: Math.round((Number(value || 0) / stats.totalPatients) * 100),
      count: Number(value || 0),
    }))
    .sort((a, b) => b.rate - a.rate)
    .slice(0, 3) : [];

  const dataGaps = dataAvailabilityData
    ? [...dataAvailabilityData]
        .filter(item => item.category !== 'Overall')
        .sort((a, b) => a.availability - b.availability)
        .slice(0, 3)
    : [];

  const coverageChartData = stats?.totalPatients ? [
    { metric: 'Echo Coverage', value: Math.round(((stats.withEcho || 0) / stats.totalPatients) * 100) },
    { metric: 'MRI Coverage', value: Math.round(((stats.withMri || 0) / stats.totalPatients) * 100) },
    { metric: 'Echo+MRI Overlap', value: Math.round(((stats.withBothEchoMri || 0) / stats.totalPatients) * 100) },
    { metric: 'Data Completeness', value: Math.round(Number(stats.dataCompleteness || 0)) },
  ] : undefined;

  const comorbidityRateData = stats?.totalPatients && comorbidities?.conditions
    ? Object.entries(comorbidities.conditions)
        .map(([key, value]) => ({
          condition: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          rate: Math.round((Number(value || 0) / stats.totalPatients) * 100),
          count: Number(value || 0),
        }))
        .sort((a, b) => b.rate - a.rate)
    : undefined;

  const completenessDistributionData = completeness?.distribution
    ? completeness.distribution.map((item: any) => ({
        category: item.range || item.category,
        count: item.count,
      }))
    : undefined;

  const registryContributionData = (ehvolStats?.totalPatients !== undefined && bhsStats?.totalPatients !== undefined)
    ? [
        { name: 'EHVol', value: ehvolStats.totalPatients, color: '#00a2dd' },
        { name: 'BHS', value: bhsStats.totalPatients, color: '#efb01b' },
      ]
    : undefined;

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-end">
            <Select value={dataset} onValueChange={(value: string) => setDataset(value as DatasetFilter)}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder="Dataset" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Registries</SelectItem>
                <SelectItem value="ehvol">EHVol</SelectItem>
                <SelectItem value="bhs">BHS</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

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
              <span className="text-green-600">
                {dataset === 'all' ? 'All Registries' : dataset === 'ehvol' ? 'EHVol Registry' : 'BHS Registry'}
              </span>
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
                  <p className="text-3xl">{Math.round(Number(stats?.dataCompleteness || 0))}%</p>
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

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Fast Facts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between"><span>Gender Balance</span><span>{maleCount || 0} M / {femaleCount || 0} F</span></div>
            <div className="flex justify-between"><span>Average Age</span><span>{stats?.averageAge || '0.0'} years</span></div>
            <div className="flex justify-between"><span>Top Nationality</span><span>{nationalityChartData?.[0]?.name || 'N/A'}</span></div>
            <div className="flex justify-between"><span>Top Burden</span><span>{conditionRates[0] ? `${conditionRates[0].condition} (${conditionRates[0].rate}%)` : 'N/A'}</span></div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Enrollment Momentum</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between"><span>Latest Month</span><span>{latestTrend?.month || 'N/A'}</span></div>
            <div className="flex justify-between"><span>New Enrollments</span><span>{latestTrend?.enrolled ?? 0}</span></div>
            <div className="flex justify-between"><span>Cumulative Total</span><span>{latestTrend?.cumulative ?? stats?.totalPatients ?? 0}</span></div>
            <div className="flex justify-between"><span>MoM Change</span><span className={momGrowth >= 0 ? 'text-green-600' : 'text-red-600'}>{momGrowth}%</span></div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Immediate Priorities</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {dataGaps.length > 0 ? dataGaps.map(item => (
              <div key={item.category} className="flex justify-between">
                <span>{item.category}</span>
                <span>{Math.round(item.availability)}% captured</span>
              </div>
            )) : (
              <div>No data quality gaps available.</div>
            )}
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
                <CardTitle>Nationality Distribution (Top Segments)</CardTitle>
              </CardHeader>
              <CardContent>
                {demoLoading ? (
                  <div className="flex items-center justify-center h-[300px]">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : nationalityChartData && nationalityChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={nationalityChartData} layout="vertical" margin={{ left: 20, right: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis type="category" dataKey="name" width={120} />
                      <Tooltip formatter={(value) => [`${value} patients`, 'Count']} />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                        {nationalityChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
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
                ) : demographicsChartData && demographicsChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={demographicsChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="ageGroup" />
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
                <CardTitle>Comorbidity Prevalence Rate</CardTitle>
              </CardHeader>
              <CardContent>
                {comorbidityLoading ? (
                  <div className="flex items-center justify-center h-[300px]">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : comorbidityRateData && comorbidityRateData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={comorbidityRateData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="condition" angle={-45} textAnchor="end" height={80} />
                      <YAxis domain={[0, 100]} />
                      <Tooltip formatter={(value, _name, payload) => [`${value}% (${payload?.payload?.count || 0} patients)`, 'Prevalence']} />
                      <Bar dataKey="rate" fill="#e9322b" name="Prevalence %" />
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
                      comorbidities: `${item.comorbidities} conditions`,
                      patients: item.patients
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
              <CardTitle>Registry Coverage Scorecard</CardTitle>
              <p className="text-sm text-muted-foreground">
                Coverage KPIs to monitor platform execution and data capture performance.
              </p>
            </CardHeader>
            <CardContent>
              {statsLoading ? (
                <div className="flex items-center justify-center h-[400px]">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              ) : coverageChartData ? (
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={coverageChartData} layout="vertical" margin={{ left: 10, right: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" domain={[0, 100]} />
                    <YAxis type="category" dataKey="metric" width={140} />
                    <Tooltip formatter={(value) => [`${value}%`, 'Coverage']} />
                    <Bar dataKey="value" fill="#00a2dd" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
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

          {dataset === 'all' && (
            <Card>
              <CardHeader>
                <CardTitle>Registry Contribution</CardTitle>
                <p className="text-sm text-muted-foreground">
                  Contribution split across participating registries.
                </p>
              </CardHeader>
              <CardContent>
                {ehvolStatsLoading || bhsStatsLoading ? (
                  <div className="flex items-center justify-center h-[280px]">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : registryContributionData ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
                    <ResponsiveContainer width="100%" height={280}>
                      <PieChart>
                        <Pie data={registryContributionData} cx="50%" cy="50%" outerRadius={90} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                          {registryContributionData.map((entry, index) => (
                            <Cell key={`mix-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => [`${value} patients`, 'Count']} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="space-y-2 text-sm">
                      {registryContributionData.map(item => {
                        const total = (ehvolStats?.totalPatients || 0) + (bhsStats?.totalPatients || 0);
                        const share = total > 0 ? Math.round((item.value / total) * 100) : 0;
                        return (
                          <div key={item.name} className="flex justify-between">
                            <span>{item.name}</span>
                            <span>{item.value.toLocaleString()} ({share}%)</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <DataNotAvailable title="Registry Contribution" message="Registry split data is not available" />
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="completeness" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                  </>
                ) : (
                  <DataNotAvailable title="Data Availability by Category" message="Data availability data is not available" />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Completeness Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                {compLoading ? (
                  <div className="flex items-center justify-center h-[300px]">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : completenessDistributionData && completenessDistributionData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={completenessDistributionData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="category" />
                      <YAxis />
                      <Tooltip formatter={(value) => [`${value} patients`, 'Count']} />
                      <Bar dataKey="count" fill="#00a2dd" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <DataNotAvailable title="Completeness Distribution" message="Completeness distribution data is not available" />
                )}
              </CardContent>
            </Card>
          </div>

          {dataAvailabilityData && dataAvailabilityData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Data Quality Benchmark Strip</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {dataAvailabilityData.map((item) => (
                    <div key={item.category} className="flex items-center justify-between text-sm">
                      <span>{item.category}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-48 bg-gray-200 rounded-full h-2">
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
              </CardContent>
            </Card>
          )}
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
              <GeographicMapping dataset={dataset} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}