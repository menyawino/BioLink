import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Slider } from "./ui/slider";
import { Switch } from "./ui/switch";
import { Label } from "./ui/label";
import { Clock, Play, Pause, RotateCcw, ZoomIn, ZoomOut, Calendar, Activity, TrendingUp } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter, AreaChart, Area, ComposedChart, Bar } from 'recharts';

interface TimelineEvent {
  id: string;
  date: string;
  type: 'clinical' | 'medication' | 'procedure' | 'lab' | 'imaging' | 'outcome';
  category: string;
  value?: number;
  description: string;
  severity?: 'low' | 'moderate' | 'high';
}

export function TimelineExplorer() {
  const [selectedPatient, setSelectedPatient] = useState("CVD-001247");
  const [timeRange, setTimeRange] = useState([0, 24]); // months
  const [showEvents, setShowEvents] = useState({
    clinical: true,
    medication: true,
    procedure: true,
    lab: true,
    imaging: true,
    outcome: true
  });
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [zoomLevel, setZoomLevel] = useState(1);

  // Mock longitudinal data
  const timelineData = [
    { date: "2023-01", biomarkers: { bnp: 95, troponin: 12.5, crp: 2.1 }, vitals: { systolic: 150, diastolic: 95, hr: 78 }, ef: 55 },
    { date: "2023-03", biomarkers: { bnp: 110, troponin: 14.2, crp: 2.8 }, vitals: { systolic: 148, diastolic: 92, hr: 82 }, ef: 53 },
    { date: "2023-06", biomarkers: { bnp: 125, troponin: 15.1, crp: 3.2 }, vitals: { systolic: 145, diastolic: 90, hr: 76 }, ef: 52 },
    { date: "2023-09", biomarkers: { bnp: 180, troponin: 18.3, crp: 4.1 }, vitals: { systolic: 142, diastolic: 88, hr: 80 }, ef: 48 },
    { date: "2023-12", biomarkers: { bnp: 320, troponin: 16.1, crp: 3.8 }, vitals: { systolic: 145, diastolic: 89, hr: 75 }, ef: 50 },
    { date: "2024-03", biomarkers: { bnp: 285, troponin: 15.2, crp: 4.2 }, vitals: { systolic: 145, diastolic: 92, hr: 78 }, ef: 52 }
  ];

  const events: TimelineEvent[] = [
    {
      id: "1",
      date: "2023-01-15",
      type: "clinical",
      category: "Diagnosis",
      description: "Essential Hypertension diagnosed",
      severity: "moderate"
    },
    {
      id: "2", 
      date: "2023-01-20",
      type: "medication",
      category: "ACE Inhibitor",
      description: "Started Lisinopril 10mg daily",
      severity: "low"
    },
    {
      id: "3",
      date: "2023-03-10",
      type: "procedure",
      category: "Echocardiogram",
      description: "Baseline cardiac function assessment",
      severity: "low"
    },
    {
      id: "4",
      date: "2023-06-15",
      type: "lab",
      category: "Biomarkers",
      value: 125,
      description: "BNP trending upward",
      severity: "moderate"
    },
    {
      id: "5",
      date: "2023-09-20",
      type: "clinical",
      category: "Symptom",
      description: "Reported shortness of breath",
      severity: "high"
    },
    {
      id: "6",
      date: "2023-10-05",
      type: "medication",
      category: "Diuretic",
      description: "Added Furosemide 20mg daily",
      severity: "moderate"
    },
    {
      id: "7",
      date: "2024-01-12",
      type: "imaging",
      category: "MRI",
      description: "Cardiac MRI shows mild dysfunction",
      severity: "moderate"
    }
  ];

  const getEventColor = (type: string) => {
    switch (type) {
      case 'clinical': return '#ef4444';
      case 'medication': return '#3b82f6';
      case 'procedure': return '#22c55e';
      case 'lab': return '#f59e0b';
      case 'imaging': return '#8b5cf6';
      case 'outcome': return '#ec4899';
      default: return '#6b7280';
    }
  };

  const getSeverityVariant = (severity?: string) => {
    switch (severity) {
      case 'high': return 'destructive';
      case 'moderate': return 'default';
      case 'low': return 'secondary';
      default: return 'outline';
    }
  };

  const toggleEventType = (type: string) => {
    setShowEvents(prev => ({
      ...prev,
      [type]: !prev[type as keyof typeof prev]
    }));
  };

  const playTimeline = () => {
    setIsPlaying(!isPlaying);
    // Animation logic would go here
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Clock className="h-5 w-5" />
            <span>Longitudinal Timeline Explorer</span>
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Interactive multi-modal data exploration with temporal visualization
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label>Patient</Label>
              <Select value={selectedPatient} onValueChange={setSelectedPatient}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="CVD-001247">CVD-001247 (Sarah Johnson)</SelectItem>
                  <SelectItem value="CVD-001248">CVD-001248 (John Smith)</SelectItem>
                  <SelectItem value="CVD-001249">CVD-001249 (Maria Garcia)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Time Range: {timeRange[0]} - {timeRange[1]} months</Label>
              <Slider
                value={timeRange}
                onValueChange={setTimeRange}
                max={60}
                min={0}
                step={1}
                className="mt-2"
              />
            </div>

            <div className="flex items-center space-x-4">
              <Button variant="outline" size="sm" onClick={playTimeline}>
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </Button>
              <Button variant="outline" size="sm">
                <RotateCcw className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm">
                <ZoomIn className="h-4 w-4" />
              </Button>
              <Button variant="outline" size="sm">
                <ZoomOut className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div>
            <Label>Event Types</Label>
            <div className="flex flex-wrap gap-3 mt-2">
              {Object.entries(showEvents).map(([type, enabled]) => (
                <div key={type} className="flex items-center space-x-2">
                  <Switch
                    checked={enabled}
                    onCheckedChange={() => toggleEventType(type)}
                  />
                  <Label className="text-sm capitalize">{type}</Label>
                  <div 
                    className="w-3 h-3 rounded" 
                    style={{ backgroundColor: getEventColor(type) }}
                  />
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Protein Biomarker Trends */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Protein Biomarker Evolution</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <ComposedChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Area yAxisId="left" dataKey="biomarkers.bnp" fill="#3b82f6" fillOpacity={0.3} stroke="#3b82f6" name="BNP" />
              <Line yAxisId="left" type="monotone" dataKey="biomarkers.troponin" stroke="#ef4444" strokeWidth={2} name="Troponin" />
              <Line yAxisId="right" type="monotone" dataKey="ef" stroke="#22c55e" strokeWidth={2} name="Ejection Fraction" />
            </ComposedChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Event Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Clinical Events Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            {/* Timeline axis */}
            <div className="absolute left-0 right-0 top-1/2 h-0.5 bg-border"></div>
            
            {/* Events */}
            <div className="space-y-4 py-8">
              {events
                .filter(event => showEvents[event.type as keyof typeof showEvents])
                .map((event, index) => (
                <div key={event.id} className={`relative flex items-center ${index % 2 === 0 ? 'justify-start' : 'justify-end'}`}>
                  <div className={`max-w-sm ${index % 2 === 0 ? 'mr-8' : 'ml-8'}`}>
                    <Card className="relative">
                      <CardContent className="p-3">
                        <div className="flex items-start justify-between mb-2">
                          <Badge variant={getSeverityVariant(event.severity)}>
                            {event.category}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {event.date}
                          </span>
                        </div>
                        <p className="text-sm">{event.description}</p>
                        {event.value && (
                          <div className="text-xs text-muted-foreground mt-1">
                            Value: {event.value}
                          </div>
                        )}
                      </CardContent>
                      
                      {/* Timeline connector */}
                      <div 
                        className={`absolute top-1/2 transform -translate-y-1/2 w-3 h-3 rounded-full ${index % 2 === 0 ? '-right-6' : '-left-6'}`}
                        style={{ backgroundColor: getEventColor(event.type) }}
                      />
                    </Card>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Vital Signs Correlation */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Vital Signs & Clinical Correlation</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <ScatterChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="vitals.systolic" name="Systolic BP" />
              <YAxis dataKey="ef" name="Ejection Fraction" />
              <Tooltip 
                formatter={(value, name) => [value, name]}
                labelFormatter={(label) => `Systolic BP: ${label}`}
              />
              <Scatter dataKey="ef" fill="#8884d8" />
            </ScatterChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Events</p>
                <p className="text-2xl">{events.length}</p>
              </div>
              <Calendar className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Follow-up Period</p>
                <p className="text-2xl">18 mo</p>
              </div>
              <Activity className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">EF Change</p>
                <p className="text-2xl text-red-500">-3%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}