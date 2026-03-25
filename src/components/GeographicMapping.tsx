import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Slider } from "./ui/slider";
import { Label } from "./ui/label";
import { Map, Layers, Download, Filter } from "lucide-react";
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getGovernorateGeographicStats, getEnrollmentTrends } from '../api/analytics';
import type { MapData, EnrollmentTrend } from '../api/types';
import type { DatasetFilter } from "../api/patients";

interface GeographicMappingProps {
  dataset?: DatasetFilter;
}

export function GeographicMapping({ dataset = 'all' }: GeographicMappingProps) {
  const [selectedLayer, setSelectedLayer] = useState("patientCount");
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [opacity, setOpacity] = useState([75]);
  const [regionData, setRegionData] = useState<MapData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [enrollmentTrends, setEnrollmentTrends] = useState<EnrollmentTrend[]>([]);
  const [trendsLoading, setTrendsLoading] = useState(true);
  const [trendsError, setTrendsError] = useState<string | null>(null);

  // Fetch geographic data from API
  useEffect(() => {
    const fetchGeographicData = async () => {
      try {
        setLoading(true);
        const response = await getGovernorateGeographicStats(dataset);
        if (response.success && response.data) {
          setRegionData(response.data);
        } else {
          setError('Failed to load geographic data');
        }
      } catch (err) {
        setError('Error fetching geographic data');
        console.error('Geographic data fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchGeographicData();
  }, [dataset]);

  // Fetch enrollment trends for the recruitment chart
  useEffect(() => {
    const fetchEnrollmentTrends = async () => {
      try {
        setTrendsLoading(true);
        const response = await getEnrollmentTrends(dataset);
        if (response.success && response.data) {
          setEnrollmentTrends(response.data);
        } else {
          setTrendsError('Failed to load enrollment trends');
        }
      } catch (err) {
        setTrendsError('Error fetching enrollment trends');
        console.error('Enrollment trends fetch error:', err);
      } finally {
        setTrendsLoading(false);
      }
    };

    fetchEnrollmentTrends();
  }, [dataset]);

  const getLayerValue = (region: MapData) => {
    switch (selectedLayer) {
      case "patientCount":
        return region.patientCount;
      case "demographics":
        return region.demographics.averageAge;
      case "riskFactors":
        return region.riskFactors.hypertension ?? 0;
      default:
        return region.patientCount;
    }
  };

  const layerOptions = [
    { value: "patientCount", label: "Patient Count", description: "Number of enrolled patients" },
    { value: "demographics", label: "Demographics", description: "Age and gender distribution" },
    { value: "riskFactors", label: "Risk Factors", description: "Regional risk factor rates" }
  ];

  const getColorForValue = (value: number, layer: string) => {
    if (layer === "patientCount") {
      if (value >= 400) return '#dc2626';
      if (value >= 250) return '#ea580c';
      if (value >= 150) return '#ca8a04';
      return '#16a34a';
    }
    if (layer === "demographics") {
      if (value >= 55) return '#dc2626';
      if (value >= 45) return '#ea580c';
      if (value >= 35) return '#ca8a04';
      return '#16a34a';
    }
    if (layer === "riskFactors") {
      if (value >= 25) return '#dc2626';
      if (value >= 15) return '#ea580c';
      if (value >= 8) return '#ca8a04';
      return '#16a34a';
    }
    return '#e5e7eb';
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Map className="h-5 w-5" />
            <span>Geographic Analysis & Recruitment Mapping</span>
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Regional distribution of patients, demographics, and risk factors
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>Data Layer</Label>
              <Select value={selectedLayer} onValueChange={setSelectedLayer}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {layerOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      <div>
                        <div>{option.label}</div>
                        <div className="text-xs text-muted-foreground">{option.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Opacity: {opacity[0]}%</Label>
              <Slider
                value={opacity}
                onValueChange={setOpacity}
                max={100}
                min={10}
                step={5}
                className="mt-2"
              />
            </div>

            <div className="flex items-end space-x-2">
              <Button variant="outline" size="sm" onClick={() => setShowFilters(!showFilters)}>
                <Filter className="h-4 w-4 mr-2" />
                Filters
              </Button>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Regional Distribution Chart */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Regional Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center h-96">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                  <p>Loading geographic data...</p>
                </div>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center h-96">
                <div className="text-center text-red-600">
                  <p className="mb-2">Error loading data</p>
                  <p className="text-sm">{error}</p>
                </div>
              </div>
            ) : regionData.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={380}>
                  <ComposedChart
                    data={regionData.map(r => ({
                      region: r.region,
                      value: getLayerValue(r),
                      patients: r.patientCount,
                    }))}
                    layout="vertical"
                    margin={{ left: 80 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="region" type="category" width={80} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar
                      dataKey="value"
                      name={layerOptions.find(o => o.value === selectedLayer)?.label ?? selectedLayer}
                      fill="#3b82f6"
                      opacity={opacity[0] / 100}
                    />
                  </ComposedChart>
                </ResponsiveContainer>

                <div className="mt-4 flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <span className="text-sm font-medium">Legend:</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 bg-green-500 rounded"></div>
                      <span className="text-xs">Low</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 bg-yellow-500 rounded"></div>
                      <span className="text-xs">Medium</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 bg-red-500 rounded"></div>
                      <span className="text-xs">High</span>
                    </div>
                  </div>
                  <Badge variant="outline">
                    {regionData.reduce((sum, r) => sum + r.patientCount, 0).toLocaleString()} Total Patients
                  </Badge>
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-muted-foreground">No geographic data available</div>
            )}
          </CardContent>
        </Card>

        {/* Regional Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {selectedRegion ? `${selectedRegion} Details` : "Regional Overview"}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2"></div>
                  <p className="text-sm text-muted-foreground">Loading regional data...</p>
                </div>
              </div>
            ) : error ? (
              <div className="text-center py-8 text-red-600">
                <p>Failed to load regional data</p>
              </div>
            ) : selectedRegion ? (
              <div className="space-y-4">
                {(() => {
                  const region = regionData.find(r => r.region === selectedRegion);
                  if (!region) return (
                    <div className="text-center py-4 text-muted-foreground">
                      <p>No data available for {selectedRegion}</p>
                    </div>
                  );
                  
                  return (
                    <>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="text-center p-2 bg-blue-50 rounded">
                          <div className="text-lg font-medium">{region.patientCount}</div>
                          <div className="text-xs text-muted-foreground">Patients</div>
                        </div>
                        <div className="text-center p-2 bg-green-50 rounded">
                          <div className="text-lg font-medium">{region.demographics.averageAge}</div>
                          <div className="text-xs text-muted-foreground">Avg Age</div>
                        </div>
                      </div>

                      <div>
                        <Label className="text-sm font-medium">Demographics</Label>
                        <div className="mt-2 space-y-1 text-sm">
                          <div>Avg Age: {region.demographics.averageAge} years</div>
                          <div>Male Ratio: {Math.round(region.demographics.genderRatio * 100)}%</div>
                        </div>
                      </div>

                      <div>
                        <Label className="text-sm font-medium">Risk Factors</Label>
                        <div className="mt-2 space-y-1">
                          {Object.entries(region.riskFactors)
                            .sort(([,a], [,b]) => b - a)
                            .map(([factor, percentage]) => (
                            <div key={factor} className="flex justify-between text-sm">
                              <span className="capitalize">{factor}</span>
                              <span>{percentage}%</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <Label className="text-sm font-medium">Vitals (Avg)</Label>
                        <div className="mt-2 space-y-1 text-sm">
                          {region.vitals.avgBmi != null && (
                            <div className="flex justify-between">
                              <span>BMI</span>
                              <span>{region.vitals.avgBmi}</span>
                            </div>
                          )}
                          {region.vitals.avgSystolicBp != null && (
                            <div className="flex justify-between">
                              <span>Systolic BP</span>
                              <span>{region.vitals.avgSystolicBp} mmHg</span>
                            </div>
                          )}
                          {region.vitals.avgHba1c != null && (
                            <div className="flex justify-between">
                              <span>HbA1c</span>
                              <span>{region.vitals.avgHba1c}%</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </>
                  );
                })()}
              </div>
            ) : (
              <div className="space-y-3">
                <div className="text-sm text-muted-foreground">
                  Click on a region to view detailed information
                </div>
                {regionData.map((region) => (
                  <div
                    key={region.region}
                    className="flex items-center justify-between p-2 hover:bg-gray-50 rounded cursor-pointer"
                    onClick={() => setSelectedRegion(region.region)}
                  >
                    <div>
                      <div className="text-sm font-medium">{region.region}</div>
                      <div className="text-xs text-muted-foreground">
                        {region.patientCount} patients
                      </div>
                    </div>
                    <Badge variant="outline">
                      {region.riskFactors.hypertension ?? 0}% HTN
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recruitment Tracking */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Patient Recruitment Progress</CardTitle>
        </CardHeader>
        <CardContent>
          {trendsLoading ? (
            <div className="flex items-center justify-center h-[300px]">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : trendsError ? (
            <div className="text-sm text-red-600">{trendsError}</div>
          ) : enrollmentTrends.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={enrollmentTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Bar yAxisId="left" dataKey="enrolled" fill="#3b82f6" name="Monthly Enrolled" />
                <Line yAxisId="right" type="monotone" dataKey="cumulative" stroke="#22c55e" strokeWidth={2} name="Cumulative" />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-sm text-muted-foreground">Enrollment trends data is not available</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}