import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Slider } from "./ui/slider";
import { Switch } from "./ui/switch";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Map, MapPin, Layers, Users, TrendingUp, Download, Filter, Info } from "lucide-react";
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip as LeafletTooltip } from "react-leaflet";
import { getGovernorateGeographicStats, getEnrollmentTrends } from '../api/analytics';
import type { MapData, EnrollmentTrend } from '../api/types';

export function GeographicMapping() {
  const [selectedLayer, setSelectedLayer] = useState("prevalence");
  const [mapType, setMapType] = useState("choropleth");
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
        const response = await getGovernorateGeographicStats();
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
  }, []);

  // Fetch enrollment trends for the recruitment chart
  useEffect(() => {
    const fetchEnrollmentTrends = async () => {
      try {
        setTrendsLoading(true);
        const response = await getEnrollmentTrends();
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
  }, []);

  const COLORS = ['#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6'];

  const getLayerValue = (region: MapData) => {
    switch (selectedLayer) {
      case "prevalence":
        return region.prevalence;
      case "patientCount":
        return region.patientCount;
      case "mortality":
        return region.outcomes.mortality;
      case "demographics":
        return region.demographics.averageAge;
      case "riskFactors":
        return region.riskFactors.hypertension;
      default:
        return region.prevalence;
    }
  };

  const layerOptions = [
    { value: "prevalence", label: "Disease Prevalence", description: "CVD prevalence by region" },
    { value: "patientCount", label: "Patient Count", description: "Number of enrolled patients" },
    { value: "mortality", label: "Mortality Rate", description: "Regional mortality outcomes" },
    { value: "demographics", label: "Demographics", description: "Age and gender distribution" },
    { value: "riskFactors", label: "Risk Factors", description: "Regional risk factor prevalence" }
  ];

  const getColorForValue = (value: number, layer: string) => {
    // Define color scales for different layers
    if (layer === "prevalence") {
      if (value >= 12) return '#dc2626';
      if (value >= 9) return '#ea580c';
      if (value >= 6) return '#ca8a04';
      return '#16a34a';
    }
    if (layer === "patientCount") {
      if (value >= 400) return '#dc2626';
      if (value >= 250) return '#ea580c';
      if (value >= 150) return '#ca8a04';
      return '#16a34a';
    }
    if (layer === "mortality") {
      if (value >= 5) return '#dc2626';
      if (value >= 3) return '#ea580c';
      if (value >= 1.5) return '#ca8a04';
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
            Dynamic visualization of disease prevalence, patient recruitment, and regional outcomes
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label>Map Layer</Label>
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
              <Label>Visualization Type</Label>
              <Select value={mapType} onValueChange={setMapType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="choropleth">Choropleth Map</SelectItem>
                  <SelectItem value="heatmap">Heat Map</SelectItem>
                  <SelectItem value="bubble">Bubble Map</SelectItem>
                  <SelectItem value="cluster">Cluster Map</SelectItem>
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
              <Button variant="outline" size="sm">
                <Layers className="h-4 w-4 mr-2" />
                Layers
              </Button>
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
        {/* Interactive Map */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Interactive Map View</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative h-96 bg-gray-100 rounded-lg overflow-hidden">
              {loading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                    <p>Loading geographic data...</p>
                  </div>
                </div>
              ) : error ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center text-red-600">
                    <p className="mb-2">Error loading map data</p>
                    <p className="text-sm">{error}</p>
                  </div>
                </div>
              ) : (
                <MapContainer
                  center={[26.8206, 30.8025]}
                  zoom={6}
                  minZoom={5}
                  maxZoom={10}
                  scrollWheelZoom
                  className="w-full h-full"
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  {regionData.map((region) => {
                    const [lng, lat] = region.coordinates;
                    const value = getLayerValue(region);
                    const color = getColorForValue(value, selectedLayer);
                    const isSelected = selectedRegion === region.region;
                    return (
                      <CircleMarker
                        key={region.region}
                        center={[lat, lng]}
                        radius={isSelected ? 10 : 8}
                        pathOptions={{ color, fillColor: color, fillOpacity: 0.7, weight: 1 }}
                        eventHandlers={{
                          click: () => setSelectedRegion(region.region)
                        }}
                      >
                        <LeafletTooltip direction="top" offset={[0, -8]} opacity={0.9}>
                          <div className="text-xs">
                            <div className="font-semibold">{region.region}</div>
                            <div>Patients: {region.patientCount}</div>
                            <div>Prevalence: {region.prevalence}%</div>
                          </div>
                        </LeafletTooltip>
                        <Popup>
                          <div className="space-y-1 text-sm">
                            <div className="font-semibold">{region.region}</div>
                            <div>Patients: {region.patientCount}</div>
                            <div>Prevalence: {region.prevalence}%</div>
                            <div>Avg Age: {region.demographics.averageAge}</div>
                            <div>Mortality: {region.outcomes.mortality}%</div>
                          </div>
                        </Popup>
                      </CircleMarker>
                    );
                  })}
                </MapContainer>
              )}
              
              {selectedRegion && !loading && !error && (
                <div className="absolute top-2 left-2 bg-white p-2 rounded shadow">
                  <div className="text-sm font-medium">{selectedRegion}</div>
                  <div className="text-xs text-muted-foreground">
                    Click markers to explore data
                  </div>
                </div>
              )}
            </div>

            {/* Legend */}
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
                {loading ? "Loading..." : regionData.reduce((sum, r) => sum + r.patientCount, 0).toLocaleString() + " Total Patients"}
              </Badge>
            </div>
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
                        <div className="text-center p-2 bg-red-50 rounded">
                          <div className="text-lg font-medium">{region.prevalence}%</div>
                          <div className="text-xs text-muted-foreground">Prevalence</div>
                        </div>
                      </div>

                      <div>
                        <Label className="text-sm font-medium">Demographics</Label>
                        <div className="mt-2 space-y-1 text-sm">
                          <div>Avg Age: {region.demographics.averageAge} years</div>
                          <div>Female: {Math.round(region.demographics.genderRatio * 100)}%</div>
                        </div>
                      </div>

                      <div>
                        <Label className="text-sm font-medium">Top Risk Factors</Label>
                        <div className="mt-2 space-y-1">
                          {Object.entries(region.riskFactors)
                            .sort(([,a], [,b]) => b - a)
                            .slice(0, 3)
                            .map(([factor, percentage]) => (
                            <div key={factor} className="flex justify-between text-sm">
                              <span className="capitalize">{factor}</span>
                              <span>{percentage}%</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <Label className="text-sm font-medium">Outcomes</Label>
                        <div className="mt-2 space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span>Mortality</span>
                            <span>{region.outcomes.mortality}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Readmission</span>
                            <span>{region.outcomes.readmission}%</span>
                          </div>
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
                      {region.prevalence}%
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

      {/* Ethnicity Distribution */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {selectedRegion ? `${selectedRegion} Ethnicity Distribution` : 'Regional Ethnicity Distribution'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {(() => {
            const region = selectedRegion
              ? regionData.find(r => r.region === selectedRegion)
              : regionData[0]; // Default to first region if none selected

            if (!region || !region.demographics?.ethnicityMix) {
              return (
                <div className="text-center py-8 text-muted-foreground">
                  <p>No ethnicity data available</p>
                </div>
              );
            }

            return (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={Object.entries(region.demographics.ethnicityMix).map(([name, value]) => ({
                        name: name.charAt(0).toUpperCase() + name.slice(1),
                        value
                      }))}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                    >
                      {Object.entries(region.demographics.ethnicityMix).map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => `${value}%`} />
                  </PieChart>
                </ResponsiveContainer>

                <div className="space-y-3">
                  <h4 className="font-medium">{region.region} Breakdown</h4>
                  {Object.entries(region.demographics.ethnicityMix).map(([ethnicity, percentage], index) => (
                    <div key={ethnicity} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div
                          className="w-3 h-3 rounded"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        />
                        <span className="text-sm capitalize">{ethnicity}</span>
                      </div>
                      <span className="text-sm">{percentage}%</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}
        </CardContent>
      </Card>
    </div>
  );
}