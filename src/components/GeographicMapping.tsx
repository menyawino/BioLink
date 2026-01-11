import { useState } from "react";
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

interface MapData {
  region: string;
  coordinates: [number, number];
  patientCount: number;
  prevalence: number;
  demographics: {
    averageAge: number;
    genderRatio: number;
    ethnicityMix: Record<string, number>;
  };
  riskFactors: Record<string, number>;
  outcomes: {
    mortality: number;
    readmission: number;
    complications: number;
  };
}

export function GeographicMapping() {
  const [selectedLayer, setSelectedLayer] = useState("prevalence");
  const [mapType, setMapType] = useState("choropleth");
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [opacity, setOpacity] = useState([75]);

  // Mock geographic data
  const regionData: MapData[] = [
    {
      region: "Northeast",
      coordinates: [-74.0, 40.7],
      patientCount: 324,
      prevalence: 8.5,
      demographics: { averageAge: 65.2, genderRatio: 0.52, ethnicityMix: { white: 45, black: 22, hispanic: 18, asian: 12, other: 3 } },
      riskFactors: { hypertension: 78, diabetes: 45, smoking: 23, obesity: 56 },
      outcomes: { mortality: 4.2, readmission: 12.8, complications: 18.5 }
    },
    {
      region: "Southeast",
      coordinates: [-84.5, 33.7],
      patientCount: 489,
      prevalence: 12.1,
      demographics: { averageAge: 62.8, genderRatio: 0.48, ethnicityMix: { white: 38, black: 35, hispanic: 15, asian: 8, other: 4 } },
      riskFactors: { hypertension: 82, diabetes: 52, smoking: 31, obesity: 64 },
      outcomes: { mortality: 5.8, readmission: 15.2, complications: 22.1 }
    },
    {
      region: "Midwest",
      coordinates: [-87.6, 41.9],
      patientCount: 267,
      prevalence: 7.8,
      demographics: { averageAge: 63.4, genderRatio: 0.51, ethnicityMix: { white: 62, black: 18, hispanic: 12, asian: 6, other: 2 } },
      riskFactors: { hypertension: 75, diabetes: 41, smoking: 28, obesity: 58 },
      outcomes: { mortality: 3.9, readmission: 11.4, complications: 16.8 }
    },
    {
      region: "Southwest",
      coordinates: [-118.2, 34.1],
      patientCount: 167,
      prevalence: 6.2,
      demographics: { averageAge: 59.1, genderRatio: 0.49, ethnicityMix: { white: 28, black: 8, hispanic: 52, asian: 10, other: 2 } },
      riskFactors: { hypertension: 71, diabetes: 38, smoking: 19, obesity: 51 },
      outcomes: { mortality: 3.2, readmission: 9.8, complications: 14.3 }
    }
  ];

  const recruitmentData = [
    { month: "Jan", enrolled: 45, target: 50, cumulative: 45 },
    { month: "Feb", enrolled: 38, target: 50, cumulative: 83 },
    { month: "Mar", enrolled: 52, target: 50, cumulative: 135 },
    { month: "Apr", enrolled: 41, target: 50, cumulative: 176 },
    { month: "May", enrolled: 47, target: 50, cumulative: 223 },
    { month: "Jun", enrolled: 54, target: 50, cumulative: 277 }
  ];

  const COLORS = ['#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6'];

  const getColorForValue = (value: number, type: string) => {
    if (type === "prevalence") {
      if (value < 7) return "#22c55e";
      if (value < 10) return "#f59e0b";
      return "#ef4444";
    }
    if (type === "patientCount") {
      if (value < 200) return "#dbeafe";
      if (value < 400) return "#3b82f6";
      return "#1e40af";
    }
    return "#6b7280";
  };

  const layerOptions = [
    { value: "prevalence", label: "Disease Prevalence", description: "CVD prevalence by region" },
    { value: "patientCount", label: "Patient Count", description: "Number of enrolled patients" },
    { value: "mortality", label: "Mortality Rate", description: "Regional mortality outcomes" },
    { value: "demographics", label: "Demographics", description: "Age and gender distribution" },
    { value: "riskFactors", label: "Risk Factors", description: "Regional risk factor prevalence" }
  ];

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
        {/* Interactive Map Placeholder */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Interactive Map View</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative h-96 bg-gray-100 rounded-lg flex items-center justify-center">
              {/* Map visualization would integrate with a mapping library like Leaflet or Mapbox */}
              <div className="text-center space-y-4">
                <Map className="h-16 w-16 mx-auto text-gray-400" />
                <div>
                  <p className="text-lg font-medium">Interactive Map</p>
                  <p className="text-sm text-muted-foreground">
                    Showing {selectedLayer} data across {regionData.length} regions
                  </p>
                </div>
              </div>

              {/* Mock region markers */}
              {regionData.map((region, index) => (
                <div
                  key={region.region}
                  className="absolute cursor-pointer"
                  style={{
                    left: `${20 + index * 20}%`,
                    top: `${30 + index * 15}%`,
                  }}
                  onClick={() => setSelectedRegion(region.region)}
                >
                  <div 
                    className="w-6 h-6 rounded-full flex items-center justify-center text-white text-xs"
                    style={{ 
                      backgroundColor: getColorForValue(
                        selectedLayer === "prevalence" ? region.prevalence : region.patientCount, 
                        selectedLayer
                      )
                    }}
                  >
                    {region.patientCount}
                  </div>
                </div>
              ))}
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
                {regionData.reduce((sum, r) => sum + r.patientCount, 0).toLocaleString()} Total Patients
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
            {selectedRegion ? (
              <div className="space-y-4">
                {(() => {
                  const region = regionData.find(r => r.region === selectedRegion);
                  if (!region) return null;
                  
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
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={recruitmentData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Bar yAxisId="left" dataKey="enrolled" fill="#3b82f6" name="Monthly Enrolled" />
              <Line yAxisId="left" type="monotone" dataKey="target" stroke="#ef4444" strokeDasharray="5 5" name="Target" />
              <Line yAxisId="right" type="monotone" dataKey="cumulative" stroke="#22c55e" strokeWidth={2} name="Cumulative" />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Ethnicity Distribution */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Regional Ethnicity Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={Object.entries(regionData[0].demographics.ethnicityMix).map(([name, value]) => ({
                    name: name.charAt(0).toUpperCase() + name.slice(1),
                    value
                  }))}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                >
                  {Object.entries(regionData[0].demographics.ethnicityMix).map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `${value}%`} />
              </PieChart>
            </ResponsiveContainer>

            <div className="space-y-3">
              <h4 className="font-medium">Northeast Region Breakdown</h4>
              {Object.entries(regionData[0].demographics.ethnicityMix).map(([ethnicity, percentage], index) => (
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
        </CardContent>
      </Card>
    </div>
  );
}