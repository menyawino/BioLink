export { ChartBuilder } from "./ChartBuilderPowerBI";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Checkbox } from "./ui/checkbox";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, ScatterChart, Scatter, PieChart, Pie, Cell, Legend } from 'recharts';
import { Download, Save, Code2, BarChart3, LineChart as LineChartIcon, PieChart as PieChartIcon, Zap, Loader2, AlertCircle } from "lucide-react";
import { useScatterData, useAgeDistribution, useGenderDistribution } from "../hooks/useCharts";
import { Alert, AlertDescription } from "./ui/alert";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { ScrollArea } from "./ui/scroll-area";

interface ChartConfig {
  type: 'bar' | 'line' | 'scatter' | 'pie';
  xAxis: string;
  yAxis: string;
  groupBy?: string;
  filters: Record<string, any>;
  title: string;
}

// Available fields from the EHVol database with type info
const availableFields = [
  { id: 'age', label: 'Age', type: 'numeric' as const },
  { id: 'gender', label: 'Gender', type: 'categorical' as const },
  { id: 'bmi', label: 'BMI', type: 'numeric' as const },
  { id: 'systolic_bp', label: 'Systolic BP', type: 'numeric' as const },
  { id: 'diastolic_bp', label: 'Diastolic BP', type: 'numeric' as const },
  { id: 'heart_rate', label: 'Heart Rate', type: 'numeric' as const },
  { id: 'hba1c', label: 'HbA1c', type: 'numeric' as const },
  { id: 'troponin_i', label: 'Troponin I', type: 'numeric' as const },
  { id: 'ef', label: 'Echo EF (%)', type: 'numeric' as const },
  { id: 'lv_ejection_fraction', label: 'MRI LV EF (%)', type: 'numeric' as const },
  { id: 'lv_mass', label: 'LV Mass', type: 'numeric' as const },
  { id: 'smoking_years', label: 'Smoking Years', type: 'numeric' as const },
];

// Define chart type requirements
const chartTypeRequirements = {
  bar: {
    description: 'Shows distribution of a single variable (counts per category/range)',
    xRequired: true,
    yRequired: false,
    xTypes: ['numeric', 'categorical'] as const,
    yTypes: [] as const,
  },
  line: {
    description: 'Shows trend of Y values across X ranges (requires both axes)',
    xRequired: true,
    yRequired: true,
    xTypes: ['numeric'] as const,
    yTypes: ['numeric'] as const,
  },
  scatter: {
    description: 'Shows correlation between two numeric variables',
    xRequired: true,
    yRequired: true,
    xTypes: ['numeric'] as const,
    yTypes: ['numeric'] as const,
  },
  pie: {
    description: 'Shows proportion distribution of a single variable',
    xRequired: true,
    yRequired: false,
    xTypes: ['numeric', 'categorical'] as const,
    yTypes: [] as const,
  },
};

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

export function LegacyChartBuilder() {
  const [chartConfig, setChartConfig] = useState<ChartConfig>({
    type: 'bar',
    xAxis: 'age',
    yAxis: '',
    title: 'Age Distribution',
    filters: {},
    groupBy: undefined
  });

  const [selectedPatients, setSelectedPatients] = useState<string[]>([]);
  const [savedCharts, setSavedCharts] = useState<ChartConfig[]>([]);
  const [showCodeDialog, setShowCodeDialog] = useState(false);

  // Get field info
  const xField = availableFields.find(f => f.id === chartConfig.xAxis);
  const yField = availableFields.find(f => f.id === chartConfig.yAxis);
  const requirements = chartTypeRequirements[chartConfig.type];
  
  // Determine if current config is valid for chart type
  const needsYAxis = requirements.yRequired;
  const xAxisValid = xField && requirements.xTypes.includes(xField.type);
  const yAxisValid = !needsYAxis || (yField && requirements.yTypes.includes(yField.type));
  const configValid = xAxisValid && yAxisValid;

  // API hooks - only fetch scatter data when we need two axes
  const { data: scatterData, isLoading: scatterLoading } = useScatterData(
    chartConfig.xAxis, 
    needsYAxis ? chartConfig.yAxis : chartConfig.xAxis // Fetch same field twice for single-axis charts
  );
  const { data: ageDistData, isLoading: ageLoading } = useAgeDistribution();
  const { data: genderDistData, isLoading: genderLoading } = useGenderDistribution();

  const updateConfig = (field: keyof ChartConfig, value: any) => {
    setChartConfig(prev => ({ ...prev, [field]: value }));
  };

  // Save chart configuration
  const saveChart = () => {
    if (savedCharts.some(c => c.title === chartConfig.title)) {
      alert(`A chart with the title "${chartConfig.title}" already exists. Please use a different title.`);
      return;
    }
    setSavedCharts(prev => [...prev, { ...chartConfig }]);
    alert(`Chart "${chartConfig.title}" saved successfully!`);
  };

  // Export chart data as CSV
  const exportData = () => {
    let data: any[] = [];
    let filename = `${chartConfig.title.replace(/\s+/g, '_')}_data.csv`;
    
    // Get the current chart data based on chart type
    if (chartConfig.type === 'bar' || chartConfig.type === 'pie') {
      data = getBarPieData();
      if (data.length > 0) {
        const csv = ['Label,Count', ...data.map(d => `"${d.label}",${d.count}`)].join('\n');
        downloadCSV(csv, filename);
      }
    } else if (chartConfig.type === 'scatter' && scatterData) {
      const xLabel = xField?.label || chartConfig.xAxis;
      const yLabel = yField?.label || chartConfig.yAxis;
      const csv = [`${xLabel},${yLabel}`, ...scatterData.map(d => `${d.x},${d.y}`)].join('\n');
      downloadCSV(csv, filename);
    } else if (chartConfig.type === 'line' && scatterData) {
      const lineData = binNumericData(scatterData);
      const xLabel = xField?.label || chartConfig.xAxis;
      const yLabel = yField?.label || chartConfig.yAxis;
      const csv = [`${xLabel} Range,Count,Average ${yLabel}`, ...lineData.map(d => `"${d.label}",${d.count},${d.average}`)].join('\n');
      downloadCSV(csv, filename);
    } else {
      alert('No data available to export');
    }
  };

  // Helper to trigger CSV download
  const downloadCSV = (csv: string, filename: string) => {
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Generate code snippet for the current chart
  const generateChartCode = () => {
    const xLabel = xField?.label || chartConfig.xAxis;
    const yLabel = yField?.label || chartConfig.yAxis;
    
    const imports = `import { ${chartConfig.type === 'bar' ? 'BarChart, Bar' : chartConfig.type === 'line' ? 'LineChart, Line' : chartConfig.type === 'scatter' ? 'ScatterChart, Scatter' : 'PieChart, Pie, Cell'}, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer${chartConfig.type === 'pie' ? ', Legend' : ''} } from 'recharts';`;
    
    let chartComponent = '';
    
    if (chartConfig.type === 'bar') {
      chartComponent = `<ResponsiveContainer width="100%" height={400}>
  <BarChart data={data}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="label" label={{ value: "${xLabel}", position: 'insideBottom', offset: -5 }} />
    <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
    <Tooltip />
    <Bar dataKey="count" fill="#3b82f6" />
  </BarChart>
</ResponsiveContainer>`;
    } else if (chartConfig.type === 'line') {
      chartComponent = `<ResponsiveContainer width="100%" height={400}>
  <LineChart data={data}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="label" label={{ value: "${xLabel} (range)", position: 'insideBottom', offset: -5 }} />
    <YAxis yAxisId="left" label={{ value: 'Average ${yLabel}', angle: -90, position: 'insideLeft' }} />
    <YAxis yAxisId="right" orientation="right" label={{ value: 'Count', angle: 90, position: 'insideRight' }} />
    <Tooltip />
    <Line yAxisId="left" type="monotone" dataKey="average" stroke="#3b82f6" strokeWidth={2} />
    <Line yAxisId="right" type="monotone" dataKey="count" stroke="#22c55e" strokeWidth={2} />
  </LineChart>
</ResponsiveContainer>`;
    } else if (chartConfig.type === 'scatter') {
      chartComponent = `<ResponsiveContainer width="100%" height={400}>
  <ScatterChart>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis type="number" dataKey="x" name="${xLabel}" label={{ value: "${xLabel}", position: 'insideBottom', offset: -5 }} />
    <YAxis type="number" dataKey="y" name="${yLabel}" label={{ value: "${yLabel}", angle: -90, position: 'insideLeft' }} />
    <Tooltip cursor={{ strokeDasharray: '3 3' }} />
    <Scatter data={data} fill="#3b82f6" />
  </ScatterChart>
</ResponsiveContainer>`;
    } else if (chartConfig.type === 'pie') {
      chartComponent = `const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'];

<ResponsiveContainer width="100%" height={400}>
  <PieChart>
    <Pie
      data={data}
      cx="50%"
      cy="50%"
      outerRadius={120}
      dataKey="count"
      nameKey="label"
      label={({ label, count, percent }) => \`\${label}: \${count} (\${(percent * 100).toFixed(0)}%)\`}
    >
      {data.map((_: any, index: number) => (
        <Cell key={\`cell-\${index}\`} fill={COLORS[index % COLORS.length]} />
      ))}
    </Pie>
    <Tooltip />
    <Legend />
  </PieChart>
</ResponsiveContainer>`;
    }
    
    return `// Chart: ${chartConfig.title}
// Type: ${chartConfig.type.toUpperCase()} CHART
// X-Axis: ${xLabel}${needsYAxis ? `\n// Y-Axis: ${yLabel}` : ''}

${imports}

// Sample data structure
const data = ${JSON.stringify(chartConfig.type === 'scatter' ? (scatterData?.slice(0, 5) || []) : getBarPieData().slice(0, 5), null, 2)};

// Chart component
${chartComponent}`;
  };

  // Helper function to bin numeric data into ranges
  const binNumericData = (data: Array<{x: number; y?: number}>, bins: number = 6) => {
    if (!data || data.length === 0) return [];
    
    const values = data.map(d => d.x).filter(v => v != null && !isNaN(v));
    if (values.length === 0) return [];
    
    const min = Math.min(...values);
    const max = Math.max(...values);
    const binSize = (max - min) / bins;
    
    const binned: Record<string, { label: string; count: number; sum: number }> = {};
    
    for (let i = 0; i < bins; i++) {
      const binMin = min + i * binSize;
      const binMax = min + (i + 1) * binSize;
      const label = `${Math.round(binMin)}-${Math.round(binMax)}`;
      binned[label] = { label, count: 0, sum: 0 };
    }
    
    data.forEach(d => {
      const val = d.x;
      if (val == null || isNaN(val)) return;
      
      const binIndex = Math.min(Math.floor((val - min) / binSize), bins - 1);
      const binMin = min + binIndex * binSize;
      const binMax = min + (binIndex + 1) * binSize;
      const label = `${Math.round(binMin)}-${Math.round(binMax)}`;
      
      if (binned[label]) {
        binned[label].count++;
        binned[label].sum += d.y ?? 0;
      }
    });
    
    return Object.values(binned).map(b => ({
      ...b,
      average: b.count > 0 ? Math.round(b.sum / b.count * 10) / 10 : 0
    }));
  };

  // Get chart data based on selected field
  const getBarPieData = () => {
    // For age field, use the age distribution API
    if (chartConfig.xAxis === 'age' && ageDistData) {
      return ageDistData.map(d => ({ label: d.age_group, count: d.count }));
    }
    // For gender field, use the gender distribution API
    if (chartConfig.xAxis === 'gender' && genderDistData) {
      return genderDistData.map(d => ({ label: d.gender, count: d.count }));
    }
    // For other numeric fields, bin the scatter data
    if (xField?.type === 'numeric' && scatterData) {
      return binNumericData(scatterData);
    }
    return [];
  };

  const renderChart = () => {
    const isLoading = scatterLoading || ageLoading || genderLoading;
    
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-96">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Loading chart data...</span>
        </div>
      );
    }

    // Check if configuration is valid for the chart type
    if (!configValid) {
      return (
        <div className="flex flex-col items-center justify-center h-96 space-y-4">
          <Alert variant="destructive" className="max-w-md">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Invalid configuration for {chartConfig.type} chart.</strong>
              <p className="mt-2 text-sm">{requirements.description}</p>
              {!xAxisValid && <p className="text-sm mt-1">• X-axis must be: {requirements.xTypes.join(' or ')}</p>}
              {needsYAxis && !yAxisValid && <p className="text-sm mt-1">• Y-axis must be: {requirements.yTypes.join(' or ')}</p>}
            </AlertDescription>
          </Alert>
        </div>
      );
    }

    // Get field labels for axis titles
    const xAxisLabel = xField?.label || chartConfig.xAxis;
    const yAxisLabel = yField?.label || chartConfig.yAxis;

    switch (chartConfig.type) {
      case 'bar': {
        const barData = getBarPieData();
        if (barData.length === 0) {
          return (
            <div className="flex items-center justify-center h-96 text-muted-foreground">
              No data available for {xAxisLabel}. Try a different variable.
            </div>
          );
        }
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" label={{ value: xAxisLabel, position: 'insideBottom', offset: -5 }} />
              <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={(value: any) => [value, 'Patient Count']} />
              <Bar dataKey="count" fill="#3b82f6" name="count" />
            </BarChart>
          </ResponsiveContainer>
        );
      }
      
      case 'line': {
        if (!scatterData || scatterData.length === 0) {
          return (
            <div className="flex items-center justify-center h-96 text-muted-foreground">
              No data available for {xAxisLabel} vs {yAxisLabel}. Try different variables.
            </div>
          );
        }
        // Bin the X values and calculate average Y for each bin
        const lineData = binNumericData(scatterData);
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={lineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" label={{ value: xAxisLabel + ' (range)', position: 'insideBottom', offset: -5 }} />
              <YAxis yAxisId="left" label={{ value: 'Average ' + yAxisLabel, angle: -90, position: 'insideLeft' }} />
              <YAxis yAxisId="right" orientation="right" label={{ value: 'Count', angle: 90, position: 'insideRight' }} />
              <Tooltip formatter={(value: any, name: string) => [value, name === 'count' ? 'Patient Count' : 'Average ' + yAxisLabel]} />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="average" stroke="#3b82f6" strokeWidth={2} name={'Avg ' + yAxisLabel} dot={{ fill: '#3b82f6' }} />
              <Line yAxisId="right" type="monotone" dataKey="count" stroke="#22c55e" strokeWidth={2} name="Count" dot={{ fill: '#22c55e' }} />
            </LineChart>
          </ResponsiveContainer>
        );
      }
      
      case 'scatter': {
        if (!scatterData || scatterData.length === 0) {
          return (
            <div className="flex items-center justify-center h-96 text-muted-foreground">
              No data available for {xAxisLabel} vs {yAxisLabel}. Try different variables.
            </div>
          );
        }
        return (
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" dataKey="x" name={xAxisLabel} label={{ value: xAxisLabel, position: 'insideBottom', offset: -5 }} />
              <YAxis type="number" dataKey="y" name={yAxisLabel} label={{ value: yAxisLabel, angle: -90, position: 'insideLeft' }} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} formatter={(value: any, name: string) => [value, name === 'x' ? xAxisLabel : yAxisLabel]} />
              <Scatter data={scatterData} fill="#3b82f6" />
            </ScatterChart>
          </ResponsiveContainer>
        );
      }
      
      case 'pie': {
        const pieData = getBarPieData();
        if (pieData.length === 0) {
          return (
            <div className="flex items-center justify-center h-96 text-muted-foreground">
              No data available for {xAxisLabel}. Try a different variable.
            </div>
          );
        }
        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={120}
                dataKey="count"
                nameKey="label"
                label={({ label, count, percent }) => `${label}: ${count} (${(percent * 100).toFixed(0)}%)`}
              >
                {pieData.map((_: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: any) => [value, 'Patient Count']} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );
      }
      
      default:
        return <div className="flex items-center justify-center h-96 text-muted-foreground">Select chart type to preview</div>;
    }
  };

  const chartTypeOptions = [
    { id: 'bar', label: 'Bar Chart', icon: BarChart3, hint: 'X only (distribution)' },
    { id: 'line', label: 'Line Chart', icon: LineChartIcon, hint: 'X + Y (trend)' },
    { id: 'scatter', label: 'Scatter Plot', icon: Zap, hint: 'X + Y (correlation)' },
    { id: 'pie', label: 'Pie Chart', icon: PieChartIcon, hint: 'X only (proportions)' }
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Chart Builder</CardTitle>
          <p className="text-sm text-muted-foreground">
            Create custom visualizations from registry data
          </p>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Chart Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Chart Title</Label>
                <Input
                  value={chartConfig.title}
                  onChange={(e) => updateConfig('title', e.target.value)}
                  placeholder="Enter chart title"
                />
              </div>

              <div>
                <Label>Chart Type</Label>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  {chartTypeOptions.map((option) => {
                    const Icon = option.icon;
                    return (
                      <Button
                        key={option.id}
                        variant={chartConfig.type === option.id ? "default" : "outline"}
                        size="sm"
                        onClick={() => updateConfig('type', option.id)}
                        className="justify-start flex-col h-auto py-2"
                      >
                        <div className="flex items-center w-full">
                          <Icon className="h-4 w-4 mr-2" />
                          {option.label}
                        </div>
                        <span className="text-[10px] text-muted-foreground font-normal w-full text-left">{option.hint}</span>
                      </Button>
                    );
                  })}
                </div>
              </div>

              <div>
                <Label>X-Axis Variable</Label>
                <Select value={chartConfig.xAxis} onValueChange={(value) => updateConfig('xAxis', value)}>
                  <SelectTrigger className={!xAxisValid ? 'border-amber-500' : ''}>
                    <SelectValue placeholder="Select X-axis variable" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableFields.map((field) => {
                      const isValid = requirements.xTypes.includes(field.type);
                      return (
                        <SelectItem key={field.id} value={field.id} className={!isValid ? 'text-muted-foreground' : ''}>
                          {field.label} ({field.type}) {!isValid && '⚠️'}
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
                {!xAxisValid && (
                  <p className="text-xs text-amber-600 mt-1">
                    {chartConfig.type} chart requires {requirements.xTypes.join(' or ')} X-axis
                  </p>
                )}
              </div>

              {/* Only show Y-Axis for charts that need it */}
              {needsYAxis && (
                <div>
                  <Label>Y-Axis Variable</Label>
                  <Select value={chartConfig.yAxis} onValueChange={(value) => updateConfig('yAxis', value)}>
                    <SelectTrigger className={needsYAxis && !yAxisValid ? 'border-amber-500' : ''}>
                      <SelectValue placeholder="Select Y-axis variable" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableFields.map((field) => {
                        const isValid = requirements.yTypes.includes(field.type);
                        return (
                          <SelectItem key={field.id} value={field.id} className={!isValid ? 'text-muted-foreground' : ''}>
                            {field.label} ({field.type}) {!isValid && '⚠️'}
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                  {!yAxisValid && (
                    <p className="text-xs text-amber-600 mt-1">
                      {chartConfig.type} chart requires {requirements.yTypes.join(' or ')} Y-axis
                    </p>
                  )}
                </div>
              )}

              {!needsYAxis && (
                <div className="p-3 bg-muted rounded-md">
                  <p className="text-xs text-muted-foreground">
                    💡 <strong>{chartConfig.type === 'bar' ? 'Bar' : 'Pie'} charts</strong> show the distribution of a single variable. 
                    Select an X-axis variable to see patient counts per category or range.
                  </p>
                </div>
              )}

              <div>
                <Label>Group By (Optional)</Label>
                <Select value={chartConfig.groupBy || "none"} onValueChange={(value) => updateConfig('groupBy', value === "none" ? undefined : value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select grouping variable" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    {availableFields.filter(f => f.type === 'categorical').map((field) => (
                      <SelectItem key={field.id} value={field.id}>
                        {field.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Filters</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <Label className="text-sm">Age Range</Label>
                <div className="flex space-x-2">
                  <Input placeholder="Min" type="number" />
                  <Input placeholder="Max" type="number" />
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-sm">Gender</Label>
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <Checkbox id="male" />
                    <Label htmlFor="male" className="text-sm">Male</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox id="female" />
                    <Label htmlFor="female" className="text-sm">Female</Label>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-sm">Risk Level</Label>
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <Checkbox id="low" />
                    <Label htmlFor="low" className="text-sm">Low</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox id="moderate" />
                    <Label htmlFor="moderate" className="text-sm">Moderate</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox id="high" />
                    <Label htmlFor="high" className="text-sm">High</Label>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button className="w-full" size="sm" onClick={saveChart} disabled={!configValid}>
                <Save className="h-4 w-4 mr-2" />
                Save Chart
              </Button>
              <Button variant="outline" className="w-full" size="sm" onClick={exportData} disabled={!configValid}>
                <Download className="h-4 w-4 mr-2" />
                Export Data
              </Button>
              <Dialog open={showCodeDialog} onOpenChange={setShowCodeDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="w-full" size="sm" disabled={!configValid}>
                    <Code2 className="h-4 w-4 mr-2" />
                    Code
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-3xl max-h-[80vh]">
                  <DialogHeader>
                    <DialogTitle>Chart Code</DialogTitle>
                  </DialogHeader>
                  <ScrollArea className="h-[60vh] w-full rounded-md border p-4">
                    <pre className="text-sm">
                      <code>{generateChartCode()}</code>
                    </pre>
                  </ScrollArea>
                </DialogContent>
              </Dialog>
            </CardContent>
          </Card>
        </div>

        {/* Chart Preview */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>{chartConfig.title}</CardTitle>
                <Badge variant="outline">
                  {selectedPatients.length > 0 ? `${selectedPatients.length} patients` : 'All patients'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {renderChart()}
            </CardContent>
          </Card>

          {/* Saved Charts */}
          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="text-base">Saved Charts</CardTitle>
            </CardHeader>
            <CardContent>
              {savedCharts.length === 0 ? (
                <div className="text-sm text-muted-foreground text-center py-8">
                  No saved charts yet. Create and save a chart to see it here.
                </div>
              ) : (
                <div className="space-y-2">
                  {savedCharts.map((chart, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent cursor-pointer" onClick={() => setChartConfig(chart)}>
                      <div className="flex-1">
                        <div className="font-medium text-sm">{chart.title}</div>
                        <div className="text-xs text-muted-foreground">
                          {chart.type} • {xField?.label || chart.xAxis}
                          {chart.yAxis && ` vs ${yField?.label || chart.yAxis}`}
                        </div>
                      </div>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSavedCharts(prev => prev.filter((_, i) => i !== index));
                        }}
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}