import { useEffect, useMemo, useState } from "react";
import type { MouseEvent } from "react";
import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Checkbox } from "./ui/checkbox";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Switch } from "./ui/switch";
import { Alert, AlertDescription } from "./ui/alert";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { ScrollArea } from "./ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "./ui/accordion";
import { Download, Save, Code2, BarChart3, LineChart as LineChartIcon, PieChart as PieChartIcon, Zap, Loader2, AlertCircle, TrendingUp } from "lucide-react";
import { useScatterData, useChartSeries } from "../hooks/useCharts";
import { SupersetProgrammatic } from "./SupersetProgrammatic";

export type ChartType =
  | "column"
  | "bar"
  | "stacked_column"
  | "stacked_bar"
  | "percent_stacked_column"
  | "percent_stacked_bar"
  | "line"
  | "smooth_line"
  | "step_line"
  | "area"
  | "stacked_area"
  | "combo"
  | "pareto"
  | "waterfall"
  | "scatter"
  | "bubble"
  | "heatmap"
  | "histogram"
  | "boxplot"
  | "lollipop"
  | "dot"
  | "pie"
  | "donut"
  | "rose"
  | "funnel"
  | "radar"
  | "treemap"
  | "sunburst"
  | "gauge"
  | "kpi";

export interface ChartConfig {
  type: ChartType;
  xAxis: string;
  yAxis: string;
  groupBy?: string;
  title: string;
  aggregation: "count" | "avg" | "sum" | "min" | "max";
  bins: number;
  topN: number;
  sortOrder: "desc" | "asc";
  stacked: boolean;
  normalize: boolean;
  smooth: boolean;
  showLabels: boolean;
  showLegend: boolean;
  showDataZoom: boolean;
  orientation: "vertical" | "horizontal";
  palette: "default" | "cool" | "warm" | "muted";
  showTrendline: boolean;
}

interface ChartRequirement {
  description: string;
  xRequired: boolean;
  yRequired: boolean;
  xTypes: Array<"numeric" | "categorical">;
  yTypes: Array<"numeric" | "categorical">;
}

const availableFields = [
  { id: "age", label: "Age", type: "numeric" as const },
  { id: "gender", label: "Gender", type: "categorical" as const },
  { id: "bmi", label: "BMI", type: "numeric" as const },
  { id: "systolic_bp", label: "Systolic BP", type: "numeric" as const },
  { id: "diastolic_bp", label: "Diastolic BP", type: "numeric" as const },
  { id: "heart_rate", label: "Heart Rate", type: "numeric" as const },
  { id: "hba1c", label: "HbA1c", type: "numeric" as const },
  { id: "troponin_i", label: "Troponin I", type: "numeric" as const },
  { id: "ef", label: "Echo EF (%)", type: "numeric" as const },
  { id: "lv_ejection_fraction", label: "MRI LV EF (%)", type: "numeric" as const },
  { id: "lv_mass", label: "LV Mass", type: "numeric" as const },
  { id: "smoking_years", label: "Smoking Years", type: "numeric" as const }
];

const SAVED_CHARTS_STORAGE_KEY = "biolink.savedCharts.v1";

const chartTypeRequirements: Record<ChartType, ChartRequirement> = {
  column: {
    description: "Column chart for distributions and comparisons",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  bar: {
    description: "Horizontal bar chart for ranked comparisons",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  stacked_column: {
    description: "Stacked columns for grouped comparisons",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  stacked_bar: {
    description: "Stacked bars for grouped comparisons",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  percent_stacked_column: {
    description: "100% stacked columns for share analysis",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  percent_stacked_bar: {
    description: "100% stacked bars for share analysis",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  line: {
    description: "Line chart for trends",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  smooth_line: {
    description: "Smoothed line for trend insights",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  step_line: {
    description: "Step line for discrete changes",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  area: {
    description: "Area chart for volume over time",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  stacked_area: {
    description: "Stacked area chart for composition",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  combo: {
    description: "Combo chart with bars and line",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  pareto: {
    description: "Pareto chart for cumulative impact",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  waterfall: {
    description: "Waterfall chart for cumulative change",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  scatter: {
    description: "Scatter plot for correlation",
    xRequired: true,
    yRequired: true,
    xTypes: ["numeric"],
    yTypes: ["numeric"]
  },
  bubble: {
    description: "Bubble plot for 3D insight",
    xRequired: true,
    yRequired: true,
    xTypes: ["numeric"],
    yTypes: ["numeric"]
  },
  heatmap: {
    description: "Heatmap for density patterns",
    xRequired: true,
    yRequired: true,
    xTypes: ["numeric"],
    yTypes: ["numeric"]
  },
  histogram: {
    description: "Histogram for numeric distributions",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric"],
    yTypes: ["numeric"]
  },
  boxplot: {
    description: "Boxplot for statistical spread",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric"],
    yTypes: ["numeric"]
  },
  lollipop: {
    description: "Lollipop chart for clean comparisons",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  dot: {
    description: "Dot plot for minimal comparisons",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  pie: {
    description: "Pie chart for composition",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  donut: {
    description: "Donut chart for composition",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  rose: {
    description: "Rose chart for radial comparison",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  funnel: {
    description: "Funnel chart for stages",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  radar: {
    description: "Radar chart for multi-category view",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  treemap: {
    description: "Treemap for hierarchical composition",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  sunburst: {
    description: "Sunburst for layered categories",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  gauge: {
    description: "Gauge for KPI",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  },
  kpi: {
    description: "KPI card for headline metrics",
    xRequired: true,
    yRequired: false,
    xTypes: ["numeric", "categorical"],
    yTypes: ["numeric"]
  }
};

const paletteMap = {
  default: ["#2563eb", "#22c55e", "#f97316", "#e11d48", "#8b5cf6", "#14b8a6", "#facc15", "#64748b"],
  cool: ["#0ea5e9", "#22d3ee", "#38bdf8", "#60a5fa", "#6366f1", "#a78bfa", "#f0abfc", "#f9a8d4"],
  warm: ["#f97316", "#fb7185", "#ef4444", "#f59e0b", "#facc15", "#84cc16", "#22c55e", "#10b981"],
  muted: ["#475569", "#64748b", "#94a3b8", "#cbd5f5", "#94a3b8", "#64748b", "#475569", "#1f2937"]
};

const chartTypeGroups = [
  {
    title: "Bars & Columns",
    items: ["column", "bar", "stacked_column", "stacked_bar", "percent_stacked_column", "percent_stacked_bar", "waterfall", "lollipop", "dot"] as ChartType[]
  },
  {
    title: "Lines & Areas",
    items: ["line", "smooth_line", "step_line", "area", "stacked_area", "combo", "pareto"] as ChartType[]
  },
  {
    title: "Scatter & Distribution",
    items: ["scatter", "bubble", "heatmap", "histogram", "boxplot"] as ChartType[]
  },
  {
    title: "Composition",
    items: ["pie", "donut", "rose", "funnel", "treemap", "sunburst", "radar"] as ChartType[]
  },
  {
    title: "KPI",
    items: ["gauge", "kpi"] as ChartType[]
  }
];

const chartTypeLabels: Record<ChartType, string> = {
  column: "Column",
  bar: "Bar",
  stacked_column: "Stacked Column",
  stacked_bar: "Stacked Bar",
  percent_stacked_column: "100% Stacked Column",
  percent_stacked_bar: "100% Stacked Bar",
  line: "Line",
  smooth_line: "Smooth Line",
  step_line: "Step Line",
  area: "Area",
  stacked_area: "Stacked Area",
  combo: "Combo",
  pareto: "Pareto",
  waterfall: "Waterfall",
  scatter: "Scatter",
  bubble: "Bubble",
  heatmap: "Heatmap",
  histogram: "Histogram",
  boxplot: "Boxplot",
  lollipop: "Lollipop",
  dot: "Dot Plot",
  pie: "Pie",
  donut: "Donut",
  rose: "Rose",
  funnel: "Funnel",
  radar: "Radar",
  treemap: "Treemap",
  sunburst: "Sunburst",
  gauge: "Gauge",
  kpi: "KPI Card"
};

const chartTypeIcons: Record<ChartType, typeof BarChart3> = {
  column: BarChart3,
  bar: BarChart3,
  stacked_column: BarChart3,
  stacked_bar: BarChart3,
  percent_stacked_column: BarChart3,
  percent_stacked_bar: BarChart3,
  line: LineChartIcon,
  smooth_line: LineChartIcon,
  step_line: LineChartIcon,
  area: LineChartIcon,
  stacked_area: LineChartIcon,
  combo: TrendingUp,
  pareto: TrendingUp,
  waterfall: TrendingUp,
  scatter: Zap,
  bubble: Zap,
  heatmap: Zap,
  histogram: BarChart3,
  boxplot: BarChart3,
  lollipop: BarChart3,
  dot: BarChart3,
  pie: PieChartIcon,
  donut: PieChartIcon,
  rose: PieChartIcon,
  funnel: PieChartIcon,
  radar: PieChartIcon,
  treemap: PieChartIcon,
  sunburst: PieChartIcon,
  gauge: PieChartIcon,
  kpi: PieChartIcon
};

const formatNumber = (value: number) => {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toFixed(1).replace(/\.0$/, "");
};

const computeTrendline = (points: Array<{ x: number; y: number }>) => {
  if (points.length < 2) return [];
  const n = points.length;
  const sumX = points.reduce((acc, p) => acc + p.x, 0);
  const sumY = points.reduce((acc, p) => acc + p.y, 0);
  const sumXY = points.reduce((acc, p) => acc + p.x * p.y, 0);
  const sumXX = points.reduce((acc, p) => acc + p.x * p.x, 0);
  const denom = n * sumXX - sumX * sumX;
  if (denom === 0) return [];
  const slope = (n * sumXY - sumX * sumY) / denom;
  const intercept = (sumY - slope * sumX) / n;
  const xs = points.map(p => p.x);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  return [
    { x: minX, y: slope * minX + intercept },
    { x: maxX, y: slope * maxX + intercept }
  ];
};

export function ChartBuilder() {
  const [chartConfig, setChartConfig] = useState<ChartConfig>({
    type: "column",
    xAxis: "age",
    yAxis: "",
    title: "Age Distribution",
    aggregation: "count",
    bins: 8,
    topN: 20,
    sortOrder: "desc",
    stacked: false,
    normalize: false,
    smooth: true,
    showLabels: false,
    showLegend: true,
    showDataZoom: true,
    orientation: "vertical",
    palette: "default",
    showTrendline: true
  });

  const [selectedPatients] = useState<string[]>([]);
  const [savedCharts, setSavedCharts] = useState<ChartConfig[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      const stored = localStorage.getItem(SAVED_CHARTS_STORAGE_KEY);
      return stored ? (JSON.parse(stored) as ChartConfig[]) : [];
    } catch {
      return [];
    }
  });
  const [showCodeDialog, setShowCodeDialog] = useState(false);
  const [galleryFilter, setGalleryFilter] = useState("");

  useEffect(() => {
    localStorage.setItem(SAVED_CHARTS_STORAGE_KEY, JSON.stringify(savedCharts));
  }, [savedCharts]);

  const xField = availableFields.find(field => field.id === chartConfig.xAxis);
  const yField = availableFields.find(field => field.id === chartConfig.yAxis);
  const requirements = chartTypeRequirements[chartConfig.type];

  const xAxisValid = !!xField && requirements.xTypes.includes(xField.type);
  const yAxisValid = !chartConfig.yAxis || (!!yField && requirements.yTypes.includes(yField.type));
  const needsNumericY = requirements.yRequired || chartConfig.aggregation !== "count";
  const hasValidYAxis = !!chartConfig.yAxis && yAxisValid;
  const configValid = xAxisValid && (!needsNumericY || hasValidYAxis);

  const needsScatter = ["scatter", "bubble", "heatmap", "boxplot"].includes(chartConfig.type);
  const scatterX = chartConfig.xAxis;
  const scatterY = requirements.yRequired ? chartConfig.yAxis : chartConfig.xAxis;

  const { data: scatterData, isLoading: scatterLoading } = useScatterData(scatterX, scatterY);

  const seriesParams = useMemo(
    () => ({
      xAxis: chartConfig.xAxis,
      ...(chartConfig.yAxis && yAxisValid ? { yAxis: chartConfig.yAxis } : {}),
      ...(chartConfig.groupBy ? { groupBy: chartConfig.groupBy } : {}),
      aggregation: chartConfig.aggregation === "count" || (chartConfig.yAxis && yAxisValid) ? chartConfig.aggregation : "count",
      bins: chartConfig.bins,
      limit: chartConfig.topN
    }),
    [chartConfig.xAxis, chartConfig.yAxis, chartConfig.groupBy, chartConfig.aggregation, chartConfig.bins, chartConfig.topN, yAxisValid]
  );

  const { data: seriesData, isLoading: seriesLoading } = useChartSeries(seriesParams, configValid && !needsScatter);

  const updateConfig = (field: keyof ChartConfig, value: any) => {
    setChartConfig(prev => ({ ...prev, [field]: value }));
  };

  const stackedTypes = new Set<ChartType>([
    "stacked_column",
    "stacked_bar",
    "percent_stacked_column",
    "percent_stacked_bar",
    "stacked_area"
  ]);

  const handleChartTypeSelect = (type: ChartType) => {
    const nextConfig: ChartConfig = { ...chartConfig, type };
    if (stackedTypes.has(type) && !chartConfig.groupBy) {
      const firstCategorical = availableFields.find(field => field.type === "categorical");
      if (firstCategorical) {
        nextConfig.groupBy = firstCategorical.id;
      }
    }
    setChartConfig(nextConfig);
  };

  const applicableGroups = useMemo(() => {
    const normalizedFilter = galleryFilter.trim().toLowerCase();
    if (!normalizedFilter) {
      return chartTypeGroups;
    }

    return chartTypeGroups
      .map(group => ({
        ...group,
        items: group.items.filter(type => {
          const label = chartTypeLabels[type].toLowerCase();
          const description = chartTypeRequirements[type].description.toLowerCase();
          return label.includes(normalizedFilter) || description.includes(normalizedFilter);
        })
      }))
      .filter(group => group.items.length > 0);
  }, [galleryFilter]);

  const normalizedSeriesData = useMemo(() => {
    if (!seriesData) return [];
    return seriesData
      .map(item => ({
        label: String(item.label ?? ""),
        value: Number(item.value ?? 0),
        series: item.series ? String(item.series) : "All"
      }))
      .filter(item => item.label);
  }, [seriesData]);

  const { categories, seriesByGroup } = useMemo(() => {
    const categorySet = new Set<string>();
    const groupSet = new Set<string>();
    normalizedSeriesData.forEach(point => {
      categorySet.add(point.label);
      groupSet.add(point.series || "All");
    });

    let categoriesList = Array.from(categorySet);
    const groupsList = Array.from(groupSet);

    const totals = categoriesList.map(category =>
      normalizedSeriesData
        .filter(point => point.label === category)
        .reduce((acc, point) => acc + point.value, 0)
    );

    categoriesList = categoriesList
      .map((category, index) => ({ category, total: totals[index] }))
      .sort((a, b) => (chartConfig.sortOrder === "asc" ? a.total - b.total : b.total - a.total))
      .slice(0, chartConfig.topN)
      .map(item => item.category);

    const categoryTotals = categoriesList.map(category =>
      normalizedSeriesData
        .filter(point => point.label === category)
        .reduce((acc, point) => acc + point.value, 0)
    );

    const series = groupsList.map(group => {
      const values = categoriesList.map((category, idx) => {
        const item = normalizedSeriesData.find(point => point.label === category && point.series === group);
        const value = item ? item.value : 0;
        if (!chartConfig.normalize) return value;
        const total = categoryTotals[idx];
        return total === 0 ? 0 : Number(((value / total) * 100).toFixed(2));
      });
      return { name: group, values };
    });

    return { categories: categoriesList, seriesByGroup: series };
  }, [normalizedSeriesData, chartConfig.sortOrder, chartConfig.topN, chartConfig.normalize]);

  const palette = paletteMap[chartConfig.palette];

  const buildOption = (): EChartsOption => {
    const baseOption: EChartsOption = {
      color: palette,
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      legend: { show: chartConfig.showLegend, type: "scroll" },
      toolbox: {
        show: true,
        feature: {
          dataZoom: { yAxisIndex: "none" },
          dataView: { readOnly: true },
          restore: {},
          saveAsImage: {}
        }
      },
      grid: { left: 40, right: 30, top: 40, bottom: 40, containLabel: true }
    };

    if (["scatter", "bubble"].includes(chartConfig.type)) {
      const scatterPoints = scatterData ?? [];
      const trendline = chartConfig.showTrendline ? computeTrendline(scatterPoints) : [];
      const scatterSeries = [
        {
          type: "scatter",
          symbolSize: chartConfig.type === "bubble" ? (value: number[]) => Math.max(8, Math.abs(value[1]) / 5) : 8,
          data: scatterPoints.map(point => [point.x, point.y])
        },
        ...(trendline.length
          ? [
              {
                type: "line",
                data: trendline.map(point => [point.x, point.y]),
                smooth: true,
                lineStyle: { type: "dashed", width: 2 },
                symbol: "none"
              }
            ]
          : [])
      ] as EChartsOption["series"];

      return {
        ...baseOption,
        tooltip: { trigger: "item" },
        xAxis: { type: "value", name: xField?.label || chartConfig.xAxis },
        yAxis: { type: "value", name: yField?.label || chartConfig.yAxis },
        series: scatterSeries
      };
    }

    if (chartConfig.type === "heatmap") {
      const points = scatterData ?? [];
      const xVals = points.map(p => p.x);
      const yVals = points.map(p => p.y);
      const xMin = Math.min(...xVals);
      const xMax = Math.max(...xVals);
      const yMin = Math.min(...yVals);
      const yMax = Math.max(...yVals);
      const bins = chartConfig.bins;
      const xStep = (xMax - xMin) / bins || 1;
      const yStep = (yMax - yMin) / bins || 1;

      const heatmap: number[][] = [];
      const xLabels = Array.from({ length: bins }, (_, idx) => `${(xMin + idx * xStep).toFixed(1)}–${(xMin + (idx + 1) * xStep).toFixed(1)}`);
      const yLabels = Array.from({ length: bins }, (_, idx) => `${(yMin + idx * yStep).toFixed(1)}–${(yMin + (idx + 1) * yStep).toFixed(1)}`);
      const grid = Array.from({ length: bins }, () => Array.from({ length: bins }, () => 0));

      points.forEach(point => {
        const xIdx = Math.min(Math.floor((point.x - xMin) / xStep), bins - 1);
        const yIdx = Math.min(Math.floor((point.y - yMin) / yStep), bins - 1);
        grid[yIdx][xIdx] += 1;
      });

      grid.forEach((row, yIdx) => {
        row.forEach((value, xIdx) => {
          heatmap.push([xIdx, yIdx, value]);
        });
      });

      return {
        ...baseOption,
        tooltip: { position: "top" },
        grid: { left: 80, right: 30, top: 40, bottom: 60, containLabel: true },
        xAxis: { type: "category", data: xLabels, name: xField?.label || chartConfig.xAxis, axisLabel: { rotate: 40 } },
        yAxis: { type: "category", data: yLabels, name: yField?.label || chartConfig.yAxis },
        visualMap: {
          min: 0,
          max: Math.max(...heatmap.map(point => point[2])),
          calculable: true,
          orient: "horizontal",
          left: "center",
          bottom: 0
        },
        series: [
          {
            type: "heatmap",
            data: heatmap,
            emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.3)" } }
          }
        ]
      };
    }

    if (chartConfig.type === "boxplot") {
      const values = (scatterData ?? []).map(point => point.x).sort((a, b) => a - b);
      if (values.length === 0) return baseOption;
      const q1 = values[Math.floor(values.length * 0.25)];
      const median = values[Math.floor(values.length * 0.5)];
      const q3 = values[Math.floor(values.length * 0.75)];
      const min = values[0];
      const max = values[values.length - 1];
      return {
        ...baseOption,
        xAxis: { type: "category", data: [xField?.label || chartConfig.xAxis] },
        yAxis: { type: "value" },
        series: [
          {
            type: "boxplot",
            data: [[min, q1, median, q3, max]]
          }
        ]
      };
    }

    if (["pie", "donut", "rose"].includes(chartConfig.type)) {
      return {
        ...baseOption,
        tooltip: { trigger: "item" },
        legend: { show: chartConfig.showLegend, orient: "vertical", left: "left" },
        series: [
          {
            type: "pie",
            radius: chartConfig.type === "donut" ? ["40%", "70%"] : "70%",
            roseType: chartConfig.type === "rose" ? "radius" : undefined,
            data: categories.map((label, idx) => ({ name: label, value: seriesByGroup[0]?.values[idx] ?? 0 })),
            label: { show: chartConfig.showLabels }
          }
        ]
      };
    }

    if (chartConfig.type === "funnel") {
      return {
        ...baseOption,
        tooltip: { trigger: "item" },
        series: [
          {
            type: "funnel",
            left: "10%",
            width: "80%",
            sort: "descending",
            data: categories.map((label, idx) => ({ name: label, value: seriesByGroup[0]?.values[idx] ?? 0 })),
            label: { show: chartConfig.showLabels }
          }
        ]
      };
    }

    if (chartConfig.type === "radar") {
      const values = seriesByGroup[0]?.values ?? [];
      const maxValue = Math.max(...values, 0) * 1.2;
      return {
        ...baseOption,
        tooltip: { trigger: "item" },
        radar: {
          indicator: categories.map((label, index) => ({ name: label, max: maxValue || values[index] || 1 }))
        },
        series: [
          {
            type: "radar",
            data: [
              {
                value: values,
                name: chartConfig.title
              }
            ]
          }
        ]
      };
    }

    if (chartConfig.type === "treemap" || chartConfig.type === "sunburst") {
      const grouped: Record<string, { name: string; children: { name: string; value: number }[] }> = {};
      const groups = seriesByGroup.map(group => group.name);
      categories.forEach((label, idx) => {
        groups.forEach((group, gIndex) => {
          const value = seriesByGroup[gIndex]?.values[idx] ?? 0;
          if (!grouped[group]) grouped[group] = { name: group, children: [] };
          grouped[group].children.push({ name: label, value });
        });
      });
      const data = Object.values(grouped);
      return {
        ...baseOption,
        tooltip: { trigger: "item" },
        series: [
          {
            type: chartConfig.type === "treemap" ? "treemap" : "sunburst",
            data: data.length ? data : categories.map((label, idx) => ({ name: label, value: seriesByGroup[0]?.values[idx] ?? 0 })),
            label: { show: chartConfig.showLabels },
            radius: chartConfig.type === "sunburst" ? [0, "90%"] : undefined
          }
        ]
      };
    }

    if (chartConfig.type === "gauge") {
      const total = seriesByGroup[0]?.values.reduce((acc, val) => acc + val, 0) ?? 0;
      return {
        ...baseOption,
        series: [
          {
            type: "gauge",
            progress: { show: true },
            axisLine: { lineStyle: { width: 12 } },
            detail: { formatter: formatNumber(total) },
            data: [{ value: total, name: chartConfig.title }]
          }
        ]
      };
    }

    if (chartConfig.type === "kpi") {
      const total = seriesByGroup[0]?.values.reduce((acc, val) => acc + val, 0) ?? 0;
      return {
        ...baseOption,
        series: [],
        graphic: [
          {
            type: "text",
            left: "center",
            top: "40%",
            style: {
              text: formatNumber(total),
              fontSize: 48,
              fontWeight: 700,
              fill: palette[0]
            }
          },
          {
            type: "text",
            left: "center",
            top: "58%",
            style: {
              text: chartConfig.title,
              fontSize: 16,
              fill: "#64748b"
            }
          }
        ]
      };
    }

    if (chartConfig.type === "pareto") {
      const totals = categories.map((category, idx) => ({
        category,
        value: seriesByGroup.reduce((acc, group) => acc + (group.values[idx] || 0), 0)
      }));
      const sorted = totals.sort((a, b) => b.value - a.value);
      const cumulative = sorted.reduce((acc: number[], item, idx) => {
        const prev = acc[idx - 1] ?? 0;
        acc.push(prev + item.value);
        return acc;
      }, []);
      const maxTotal = cumulative[cumulative.length - 1] || 1;
      return {
        ...baseOption,
        tooltip: { trigger: "axis" },
        xAxis: { type: "category", data: sorted.map(item => item.category) },
        yAxis: [
          { type: "value", name: "Value" },
          { type: "value", name: "Cumulative %", max: 100 }
        ],
        series: [
          {
            type: "bar",
            data: sorted.map(item => item.value),
            name: "Value"
          },
          {
            type: "line",
            yAxisIndex: 1,
            data: cumulative.map(value => Number(((value / maxTotal) * 100).toFixed(1))),
            name: "Cumulative"
          }
        ]
      };
    }

    if (chartConfig.type === "waterfall") {
      const totals = categories.map((category, idx) => ({
        category,
        value: seriesByGroup.reduce((acc, group) => acc + (group.values[idx] || 0), 0)
      }));
      const cumulative = totals.reduce((acc: number[], item, idx) => {
        const prev = acc[idx - 1] ?? 0;
        acc.push(prev + item.value);
        return acc;
      }, []);
      const helper = cumulative.map((val, idx) => val - totals[idx].value);
      return {
        ...baseOption,
        xAxis: { type: "category", data: totals.map(item => item.category) },
        yAxis: { type: "value" },
        series: [
          {
            type: "bar",
            stack: "total",
            itemStyle: { borderColor: "transparent", color: "transparent" },
            data: helper
          },
          {
            type: "bar",
            stack: "total",
            data: totals.map(item => item.value)
          }
        ]
      };
    }

    const enforcedHorizontal = ["bar", "stacked_bar", "percent_stacked_bar"].includes(chartConfig.type);
    const enforcedVertical = ["column", "stacked_column", "percent_stacked_column", "histogram"].includes(chartConfig.type);
    const isHorizontal = enforcedHorizontal || (!enforcedVertical && chartConfig.orientation === "horizontal");
    const shouldStack = chartConfig.stacked || ["stacked_column", "stacked_bar", "stacked_area", "percent_stacked_bar", "percent_stacked_column"].includes(chartConfig.type);
    const isPercent = chartConfig.normalize || ["percent_stacked_bar", "percent_stacked_column"].includes(chartConfig.type);
    const isLine = ["line", "smooth_line", "step_line", "area", "stacked_area"].includes(chartConfig.type);

    if (chartConfig.type === "lollipop") {
      return {
        ...baseOption,
        tooltip: { trigger: "axis" },
        xAxis: { type: "category", data: categories, axisLabel: { rotate: 20 } },
        yAxis: { type: "value" },
        series: [
          {
            type: "bar",
            data: seriesByGroup[0]?.values ?? [],
            barWidth: 2,
            itemStyle: { opacity: 0.4 }
          },
          {
            type: "scatter",
            data: seriesByGroup[0]?.values ?? [],
            symbolSize: 10
          }
        ]
      };
    }

    if (chartConfig.type === "dot") {
      return {
        ...baseOption,
        tooltip: { trigger: "axis" },
        xAxis: { type: "category", data: categories, axisLabel: { rotate: 20 } },
        yAxis: { type: "value" },
        series: [
          {
            type: "scatter",
            data: seriesByGroup[0]?.values ?? [],
            symbolSize: 10
          }
        ]
      };
    }

    const series = seriesByGroup.map(group => {
      const seriesType = chartConfig.type === "combo" || chartConfig.type === "pareto" ? "bar" : isLine ? "line" : "bar";
      return {
        name: group.name,
        type: seriesType,
        stack: shouldStack ? "total" : undefined,
        data: group.values,
        smooth: chartConfig.smooth || chartConfig.type === "smooth_line",
        step: chartConfig.type === "step_line" ? "middle" : false,
        areaStyle: chartConfig.type === "area" || chartConfig.type === "stacked_area" ? { opacity: 0.2 } : undefined,
        label: { show: chartConfig.showLabels, formatter: isPercent ? "{c}%" : undefined },
        barGap: chartConfig.type === "histogram" ? "0%" : undefined
      };
    }) as Array<Record<string, unknown>>;

    if (chartConfig.type === "combo") {
      const totals = categories.map((_, idx) => seriesByGroup.reduce((acc, group) => acc + (group.values[idx] || 0), 0));
      series.push({
        name: "Total",
        type: "line",
        smooth: true,
        data: totals,
        stack: undefined,
        step: false,
        areaStyle: undefined,
        label: { show: false }
      });
    }

    const option: EChartsOption = {
      ...baseOption,
      tooltip: { trigger: "axis" },
      xAxis: isHorizontal
        ? { type: "value", name: isPercent ? "%" : undefined }
        : { type: "category", data: categories, name: xField?.label || chartConfig.xAxis, axisLabel: { rotate: 20 } },
      yAxis: isHorizontal
        ? { type: "category", data: categories, name: xField?.label || chartConfig.xAxis }
        : { type: "value", name: isPercent ? "%" : undefined },
      series: series as EChartsOption["series"]
    };

    if (chartConfig.showDataZoom && categories.length > 10 && !isHorizontal) {
      option.dataZoom = [
        { type: "slider", start: 0, end: Math.min(60, (10 / categories.length) * 100) },
        { type: "inside" }
      ];
    }

    return option;
  };

  const chartOption = useMemo(buildOption, [
    chartConfig,
    palette,
    categories,
    seriesByGroup,
    scatterData,
    xField?.label,
    yField?.label
  ]);

  const saveChart = () => {
    if (savedCharts.some(c => c.title === chartConfig.title)) {
      alert(`A chart with the title "${chartConfig.title}" already exists. Please use a different title.`);
      return;
    }
    setSavedCharts(prev => [...prev, { ...chartConfig }]);
    alert(`Chart "${chartConfig.title}" saved successfully!`);
  };

  const downloadCSV = (csv: string, filename: string) => {
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportData = () => {
    const filename = `${chartConfig.title.replace(/\s+/g, "_")}_data.csv`;
    if (needsScatter) {
      const rows = (scatterData ?? []).map(point => `${point.x},${point.y}`);
      const csv = [`${xField?.label || chartConfig.xAxis},${yField?.label || chartConfig.yAxis}`, ...rows].join("\n");
      downloadCSV(csv, filename);
      return;
    }

    const rows = categories.map((label, idx) => {
      const values = seriesByGroup.map(group => group.values[idx] ?? 0);
      return [label, ...values].join(",");
    });
    const header = ["Category", ...seriesByGroup.map(group => group.name)].join(",");
    const csv = [header, ...rows].join("\n");
    downloadCSV(csv, filename);
  };

  const generateChartCode = () => {
    return `// Chart: ${chartConfig.title}\n// Type: ${chartConfig.type}\n\nconst option = ${JSON.stringify(chartOption, null, 2)};`;
  };

  const renderChart = () => {
    const isLoading = scatterLoading || seriesLoading;

    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-96">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">Loading chart data...</span>
        </div>
      );
    }

    if (!configValid) {
      return (
        <div className="flex flex-col items-center justify-center h-96 space-y-4">
          <Alert variant="destructive" className="max-w-md">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Invalid configuration for {chartConfig.type} chart.</strong>
              <p className="mt-2 text-sm">{requirements.description}</p>
              {!xAxisValid && <p className="text-sm mt-1">• X-axis must be: {requirements.xTypes.join(" or ")}</p>}
              {needsNumericY && !hasValidYAxis && <p className="text-sm mt-1">• Select a numeric Y-axis for aggregation or this chart type</p>}
            </AlertDescription>
          </Alert>
        </div>
      );
    }

    if (!needsScatter && categories.length === 0) {
      return (
        <div className="flex items-center justify-center h-96 text-muted-foreground">
          No data available. Try a different variable.
        </div>
      );
    }

    if (needsScatter && (!scatterData || scatterData.length === 0)) {
      return (
        <div className="flex items-center justify-center h-96 text-muted-foreground">
          No data available for {xField?.label || chartConfig.xAxis} vs {yField?.label || chartConfig.yAxis}. Try different variables.
        </div>
      );
    }

    return (
      <ReactECharts
        key={`${chartConfig.type}-${chartConfig.xAxis}-${chartConfig.yAxis}-${chartConfig.groupBy}-${chartConfig.aggregation}`}
        option={chartOption}
        style={{ height: 420 }}
        notMerge
      />
    );
  };

  return (
        <div className="space-y-6">
        <Tabs defaultValue="superset" className="space-y-4">
          <TabsList className="grid grid-cols-2 w-full">
            <TabsTrigger value="builder">Chart Builder</TabsTrigger>
            <TabsTrigger value="superset">Superset Dashboards</TabsTrigger>
        </TabsList>

        <TabsContent value="builder" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="space-y-4">
              <Tabs defaultValue="visuals" className="space-y-4">
                <TabsList className="grid grid-cols-2">
                  <TabsTrigger value="visuals">Visuals</TabsTrigger>
                  <TabsTrigger value="customize">Customize</TabsTrigger>
                </TabsList>

                <TabsContent value="visuals" className="space-y-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Visual Gallery</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-1">
                        <Label htmlFor="visual-gallery-filter" className="text-xs uppercase tracking-widest text-muted-foreground">
                          Filter visuals
                        </Label>
                        <Input
                          id="visual-gallery-filter"
                          value={galleryFilter}
                          onChange={event => setGalleryFilter(event.target.value)}
                          placeholder="Search by name or description"
                          className="w-full"
                        />
                      </div>
                      <ScrollArea className="h-[520px] pr-2">
                        {applicableGroups.length === 0 ? (
                          <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
                            No visuals match your filter. Try a different keyword.
                          </div>
                        ) : (
                          <div className="space-y-4">
                            {applicableGroups.map(group => (
                              <div key={group.title} className="space-y-2">
                                <div className="text-xs uppercase text-muted-foreground">{group.title}</div>
                                <div className="grid grid-cols-2 gap-2">
                                  {group.items.map(type => {
                                    const Icon = chartTypeIcons[type];
                                    const requirement = chartTypeRequirements[type];
                                    const badges = [
                                      requirement.xRequired ? "X required" : "X optional",
                                      `X: ${requirement.xTypes.join(", ")}`,
                                      requirement.yRequired ? "Y required" : "Y optional",
                                      `Y: ${requirement.yTypes.join(", ")}`
                                    ];
                                    return (
                                      <Button
                                        key={type}
                                        variant={chartConfig.type === type ? "default" : "outline"}
                                        size="sm"
                                        onClick={() => handleChartTypeSelect(type)}
                                        className="justify-start flex-col h-auto py-2 min-h-[68px] text-left"
                                        aria-label={`${chartTypeLabels[type]} chart · ${requirement.description}`}
                                      >
                                        <div className="flex items-center w-full">
                                          <Icon className="h-4 w-4 mr-2" />
                                          {chartTypeLabels[type]}
                                        </div>
                                        <span className="text-[10px] text-muted-foreground font-normal w-full text-left line-clamp-2 break-words">
                                          {requirement.description}
                                        </span>
                                        <div className="flex flex-wrap gap-1 mt-2 w-full">
                                          {badges.map(badge => (
                                            <Badge key={`${type}-${badge}`} variant="outline" className="text-[9px] uppercase tracking-widest">
                                              {badge}
                                            </Badge>
                                          ))}
                                        </div>
                                      </Button>
                                    );
                                  })}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </ScrollArea>
                    </CardContent>
                  </Card>
                </TabsContent>

            <TabsContent value="customize" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Chart Setup</CardTitle>
                </CardHeader>
                <CardContent>
                  <Accordion type="multiple" defaultValue={["fields", "options"]} className="space-y-2">
                    <AccordionItem value="fields">
                      <AccordionTrigger>Fields</AccordionTrigger>
                      <AccordionContent className="space-y-4">
                        <div>
                          <Label>Chart Title</Label>
                          <Input value={chartConfig.title} onChange={event => updateConfig("title", event.target.value)} placeholder="Enter chart title" />
                        </div>

                        <div>
                          <Label>X-Axis / Category</Label>
                          <Select value={chartConfig.xAxis} onValueChange={(value: string) => updateConfig("xAxis", value)}>
                            <SelectTrigger className={!xAxisValid ? "border-amber-500" : ""}>
                              <SelectValue placeholder="Select X-axis variable" />
                            </SelectTrigger>
                            <SelectContent>
                              {availableFields.map(field => {
                                const isValid = requirements.xTypes.includes(field.type);
                                return (
                                  <SelectItem key={field.id} value={field.id} className={!isValid ? "text-muted-foreground" : ""}>
                                    {field.label} ({field.type}) {!isValid && "⚠️"}
                                  </SelectItem>
                                );
                              })}
                            </SelectContent>
                          </Select>
                        </div>

                        <div>
                          <Label>Y-Axis / Value</Label>
                          <Select
                            value={chartConfig.yAxis || "none"}
                            onValueChange={(value: string) => {
                              const nextValue = value === "none" ? "" : value;
                              const shouldShiftAggregation = nextValue && chartConfig.aggregation === "count";
                              setChartConfig(prev => ({
                                ...prev,
                                yAxis: nextValue,
                                aggregation: shouldShiftAggregation ? "avg" : prev.aggregation
                              }));
                            }}
                          >
                            <SelectTrigger className={needsNumericY && !hasValidYAxis ? "border-amber-500" : ""}>
                              <SelectValue placeholder="Select Y-axis variable" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">None</SelectItem>
                              {availableFields.map(field => {
                                const isValid = field.type === "numeric";
                                return (
                                  <SelectItem key={field.id} value={field.id} className={!isValid ? "text-muted-foreground" : ""}>
                                    {field.label} ({field.type}) {!isValid && "⚠️"}
                                  </SelectItem>
                                );
                              })}
                            </SelectContent>
                          </Select>
                          {needsNumericY && !hasValidYAxis && (
                            <p className="text-xs text-amber-600 mt-1">
                              Select a numeric value for Y-axis when using aggregations or scatter-style visuals.
                            </p>
                          )}
                        </div>

                        <div>
                          <Label>Legend / Group By</Label>
                          <Select value={chartConfig.groupBy || "none"} onValueChange={(value: string) => updateConfig("groupBy", value === "none" ? undefined : value)}>
                            <SelectTrigger>
                              <SelectValue placeholder="Select grouping variable" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">None</SelectItem>
                              {availableFields.filter(field => field.type === "categorical").map(field => (
                                <SelectItem key={field.id} value={field.id}>
                                  {field.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          {stackedTypes.has(chartConfig.type) && !chartConfig.groupBy && (
                            <p className="text-xs text-amber-600 mt-1">
                              Stacked visuals need a Group By field to split series.
                            </p>
                          )}
                        </div>
                      </AccordionContent>
                    </AccordionItem>

                    <AccordionItem value="options">
                      <AccordionTrigger>Visual Options</AccordionTrigger>
                      <AccordionContent className="space-y-4">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <Label>Aggregation</Label>
                            <Select value={chartConfig.aggregation} onValueChange={(value: ChartConfig["aggregation"]) => updateConfig("aggregation", value)}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="count">Count</SelectItem>
                                <SelectItem value="avg">Average</SelectItem>
                                <SelectItem value="sum">Sum</SelectItem>
                                <SelectItem value="min">Min</SelectItem>
                                <SelectItem value="max">Max</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>

                          <div>
                            <Label>Top N</Label>
                            <Input type="number" value={chartConfig.topN} min={5} max={200} onChange={event => updateConfig("topN", Number(event.target.value))} />
                          </div>
                        </div>

                        {xField?.type === "numeric" && (
                          <div>
                            <Label>Bins</Label>
                            <Input type="number" value={chartConfig.bins} min={2} max={50} onChange={event => updateConfig("bins", Number(event.target.value))} />
                          </div>
                        )}

                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex items-center justify-between">
                            <Label>Stacked</Label>
                            <Switch checked={chartConfig.stacked} onCheckedChange={(value: boolean) => updateConfig("stacked", value)} />
                          </div>
                          <div className="flex items-center justify-between">
                            <Label>100% Normalize</Label>
                            <Switch checked={chartConfig.normalize} onCheckedChange={(value: boolean) => updateConfig("normalize", value)} />
                          </div>
                          <div className="flex items-center justify-between">
                            <Label>Smooth</Label>
                            <Switch checked={chartConfig.smooth} onCheckedChange={(value: boolean) => updateConfig("smooth", value)} />
                          </div>
                          <div className="flex items-center justify-between">
                            <Label>Labels</Label>
                            <Switch checked={chartConfig.showLabels} onCheckedChange={(value: boolean) => updateConfig("showLabels", value)} />
                          </div>
                          <div className="flex items-center justify-between">
                            <Label>Legend</Label>
                            <Switch checked={chartConfig.showLegend} onCheckedChange={(value: boolean) => updateConfig("showLegend", value)} />
                          </div>
                          <div className="flex items-center justify-between">
                            <Label>Zoom</Label>
                            <Switch checked={chartConfig.showDataZoom} onCheckedChange={(value: boolean) => updateConfig("showDataZoom", value)} />
                          </div>
                          <div className="flex items-center justify-between">
                            <Label>Trendline</Label>
                            <Switch checked={chartConfig.showTrendline} onCheckedChange={(value: boolean) => updateConfig("showTrendline", value)} />
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <Label>Sort Order</Label>
                            <Select value={chartConfig.sortOrder} onValueChange={(value: ChartConfig["sortOrder"]) => updateConfig("sortOrder", value)}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="desc">Descending</SelectItem>
                                <SelectItem value="asc">Ascending</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <Label>Orientation</Label>
                            <Select value={chartConfig.orientation} onValueChange={(value: ChartConfig["orientation"]) => updateConfig("orientation", value)}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="vertical">Vertical</SelectItem>
                                <SelectItem value="horizontal">Horizontal</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>

                        <div>
                          <Label>Palette</Label>
                          <Select value={chartConfig.palette} onValueChange={(value: ChartConfig["palette"]) => updateConfig("palette", value)}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="default">Default</SelectItem>
                              <SelectItem value="cool">Cool</SelectItem>
                              <SelectItem value="warm">Warm</SelectItem>
                              <SelectItem value="muted">Muted</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </AccordionContent>
                    </AccordionItem>

                    <AccordionItem value="filters">
                      <AccordionTrigger>Filters</AccordionTrigger>
                      <AccordionContent className="space-y-3">
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
                      </AccordionContent>
                    </AccordionItem>

                    <AccordionItem value="actions">
                      <AccordionTrigger>Actions</AccordionTrigger>
                      <AccordionContent className="space-y-2">
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
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>{chartConfig.title}</CardTitle>
                <Badge variant="outline">
                  {selectedPatients.length > 0 ? `${selectedPatients.length} patients` : "All patients"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>{renderChart()}</CardContent>
          </Card>

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
                  {savedCharts.map((chart, index) => {
                    const xLabel = availableFields.find(field => field.id === chart.xAxis)?.label || chart.xAxis;
                    const yLabel = availableFields.find(field => field.id === chart.yAxis)?.label || chart.yAxis;
                    return (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent cursor-pointer" onClick={() => setChartConfig(chart)}>
                        <div className="flex-1">
                          <div className="font-medium text-sm">{chart.title}</div>
                          <div className="text-xs text-muted-foreground">
                            {chartTypeLabels[chart.type]} • {xLabel}
                            {chart.yAxis && ` vs ${yLabel}`}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(event: MouseEvent<HTMLButtonElement>) => {
                            event.stopPropagation();
                            setSavedCharts(prev => prev.filter((_, i) => i !== index));
                          }}
                        >
                          Remove
                        </Button>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </TabsContent>

    <TabsContent value="superset">
      <Card>
        <CardHeader>
          <div className="space-y-1">
            <CardTitle className="text-base">Superset Dashboards</CardTitle>
            <p className="text-sm text-muted-foreground">
              Superset powers the primary dashboard experience. Use the builder to prototype tiles and then deploy through the programmatic interface below.
            </p>
          </div>
        </CardHeader>
        <CardContent>
          <SupersetProgrammatic />
        </CardContent>
      </Card>
    </TabsContent>
  </Tabs>
  </div>
  );
}
