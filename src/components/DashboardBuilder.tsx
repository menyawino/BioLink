import { useCallback, useEffect, useMemo, useState } from "react";
import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts";
import { Responsive, WidthProvider, type Layout } from "react-grid-layout";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Badge } from "./ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { ScrollArea } from "./ui/scroll-area";
import { Download, Plus, Trash2, Filter } from "lucide-react";
import { useChartSeries, useScatterData } from "../hooks/useCharts";
import type { ChartConfig, ChartType } from "./ChartBuilderPowerBI";

const ResponsiveGridLayout = WidthProvider(Responsive);

const DASHBOARD_STORAGE_KEY = "biolink.dashboard.canvas.v1";
const SAVED_CHARTS_STORAGE_KEY = "biolink.savedCharts.v1";

interface DashboardFilter {
  field: string;
  operator: "=" | "!=";
  value: string;
}

interface DashboardPanel {
  id: string;
  title: string;
  chartConfig?: ChartConfig;
  supersetUrl?: string;
}

interface DashboardState {
  name: string;
  panels: DashboardPanel[];
  layouts: Layout[];
  filters: DashboardFilter[];
}

const palettes = {
  default: ["#2563eb", "#10b981", "#f97316", "#ef4444", "#8b5cf6", "#14b8a6"],
  cool: ["#0ea5e9", "#38bdf8", "#22d3ee", "#2dd4bf", "#a5f3fc"],
  warm: ["#f97316", "#fb7185", "#facc15", "#f59e0b", "#fda4af"],
  muted: ["#64748b", "#94a3b8", "#a8a29e", "#9ca3af", "#cbd5f5"]
};

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
  dot: "Dot",
  pie: "Pie",
  donut: "Donut",
  rose: "Rose",
  funnel: "Funnel",
  radar: "Radar",
  treemap: "Treemap",
  sunburst: "Sunburst",
  gauge: "Gauge",
  kpi: "KPI"
};

const defaultDashboard: DashboardState = {
  name: "Clinical Analytics Canvas",
  panels: [],
  layouts: [],
  filters: []
};

const createPanelLayout = (id: string, index: number): Layout => ({
  i: id,
  x: (index * 4) % 12,
  y: Infinity,
  w: 4,
  h: 6,
  minW: 3,
  minH: 4
});

const buildSeriesOption = (chartConfig: ChartConfig, seriesData: Array<{ label: string; value: number; series?: string }>): EChartsOption => {
  const palette = palettes[chartConfig.palette] ?? palettes.default;
  const normalizedSeries = seriesData.map(item => ({
    label: String(item.label ?? ""),
    value: Number(item.value ?? 0),
    series: item.series ? String(item.series) : "All"
  }));

  const categories = Array.from(new Set(normalizedSeries.map(item => item.label))).filter(Boolean);
  const groupNames = Array.from(new Set(normalizedSeries.map(item => item.series)));

  const seriesByGroup = groupNames.map(group => {
    const values = categories.map(category => {
      const point = normalizedSeries.find(item => item.series === group && item.label === category);
      return point ? point.value : 0;
    });
    return { name: group, values };
  });

  const shouldStack = chartConfig.stacked || ["stacked_column", "stacked_bar", "percent_stacked_column", "percent_stacked_bar", "stacked_area"].includes(chartConfig.type);
  const isPercent = chartConfig.normalize || ["percent_stacked_column", "percent_stacked_bar"].includes(chartConfig.type);
  const isHorizontal = chartConfig.orientation === "horizontal" || ["bar", "stacked_bar", "percent_stacked_bar"].includes(chartConfig.type);
  const isLine = ["line", "smooth_line", "step_line", "area", "stacked_area"].includes(chartConfig.type);

  const normalizedSeriesByGroup = isPercent
    ? seriesByGroup.map(group => ({
        ...group,
        values: group.values.map((value, idx) => {
          const total = seriesByGroup.reduce((acc, g) => acc + (g.values[idx] || 0), 0);
          return total === 0 ? 0 : Number(((value / total) * 100).toFixed(2));
        })
      }))
    : seriesByGroup;

  if (["pie", "donut", "rose"].includes(chartConfig.type)) {
    const pieData = normalizedSeriesByGroup[0]?.values.map((value, idx) => ({
      name: categories[idx],
      value
    })) ?? [];

    return {
      color: palette,
      tooltip: { trigger: "item" },
      series: [
        {
          type: "pie",
          radius: chartConfig.type === "donut" ? ["45%", "70%"] : chartConfig.type === "rose" ? ["20%", "80%"] : "65%",
          roseType: chartConfig.type === "rose" ? "radius" : undefined,
          data: pieData,
          label: { show: chartConfig.showLabels }
        }
      ]
    };
  }

  if (chartConfig.type === "heatmap") {
    const yCategories = groupNames.length > 1 ? groupNames : ["All"];
    const matrixData = [] as Array<[number, number, number]>;
    categories.forEach((category, xIdx) => {
      yCategories.forEach((group, yIdx) => {
        const value = normalizedSeries.find(item => item.label === category && item.series === group)?.value ?? 0;
        matrixData.push([xIdx, yIdx, value]);
      });
    });

    return {
      tooltip: { position: "top" },
      grid: { height: "70%", top: 30 },
      xAxis: { type: "category", data: categories },
      yAxis: { type: "category", data: yCategories },
      visualMap: {
        min: 0,
        max: Math.max(...matrixData.map(item => item[2]), 1),
        calculable: true,
        orient: "horizontal",
        left: "center",
        bottom: 0
      },
      series: [
        {
          type: "heatmap",
          data: matrixData,
          label: { show: chartConfig.showLabels }
        }
      ]
    };
  }

  const baseOption: EChartsOption = {
    color: palette,
    tooltip: { trigger: "axis" },
    legend: { show: chartConfig.showLegend },
    grid: { left: 40, right: 20, top: 40, bottom: 40, containLabel: true }
  };

  const series = normalizedSeriesByGroup.map(group => ({
    name: group.name,
    type: isLine ? "line" : "bar",
    data: group.values,
    stack: shouldStack ? "total" : undefined,
    smooth: chartConfig.type === "smooth_line" || chartConfig.smooth,
    step: chartConfig.type === "step_line" ? "middle" : false,
    areaStyle: chartConfig.type === "area" || chartConfig.type === "stacked_area" ? { opacity: 0.25 } : undefined,
    label: { show: chartConfig.showLabels, formatter: isPercent ? "{c}%" : undefined }
  }));

  if (chartConfig.type === "combo" && series.length > 0) {
    const totals = categories.map((_, idx) => normalizedSeriesByGroup.reduce((acc, group) => acc + (group.values[idx] || 0), 0));
    series.push({
      name: "Total",
      type: "line",
      data: totals,
      smooth: true,
      label: { show: false }
    });
  }

  return {
    ...baseOption,
    xAxis: isHorizontal ? { type: "value" } : { type: "category", data: categories },
    yAxis: isHorizontal ? { type: "category", data: categories } : { type: "value" },
    series
  };
};

const PanelChart = ({
  panel,
  filters,
  onFilter
}: {
  panel: DashboardPanel;
  filters: DashboardFilter[];
  onFilter: (filter: DashboardFilter) => void;
}) => {
  const chartConfig = panel.chartConfig;

  const seriesParams = useMemo(() => {
    if (!chartConfig) return null;
    return {
      xAxis: chartConfig.xAxis,
      ...(chartConfig.yAxis ? { yAxis: chartConfig.yAxis } : {}),
      ...(chartConfig.groupBy ? { groupBy: chartConfig.groupBy } : {}),
      aggregation: chartConfig.aggregation,
      bins: chartConfig.bins,
      limit: chartConfig.topN,
      filters
    };
  }, [chartConfig, filters]);

  const needsScatter = chartConfig ? ["scatter", "bubble"].includes(chartConfig.type) : false;
  const { data: seriesData, isLoading } = useChartSeries(seriesParams ?? { xAxis: "age" }, !!seriesParams && !needsScatter);
  const { data: scatterData, isLoading: scatterLoading } = useScatterData(chartConfig?.xAxis ?? "", chartConfig?.yAxis ?? "");

  if (!chartConfig) {
    return <div className="text-sm text-muted-foreground">No chart selected.</div>;
  }

  if (panel.supersetUrl) {
    return (
      <iframe
        title={panel.title}
        src={panel.supersetUrl}
        className="w-full h-full rounded-md border"
      />
    );
  }

  if (needsScatter) {
    if (!chartConfig.yAxis) {
      return <div className="text-sm text-muted-foreground">Select a Y-axis to render scatter.</div>;
    }
    if (scatterLoading) {
      return <div className="text-sm text-muted-foreground">Loading chart...</div>;
    }

    const scatterOption: EChartsOption = {
      tooltip: { trigger: "item" },
      xAxis: { type: "value" },
      yAxis: { type: "value" },
      series: [
        {
          type: "scatter",
          data: (scatterData ?? []).map(point => [point.x, point.y]),
          symbolSize: chartConfig.type === "bubble" ? 12 : 8
        }
      ]
    };

    return (
      <ReactECharts
        option={scatterOption}
        style={{ height: "100%", width: "100%" }}
        onEvents={{
          click: (params: any) => {
            if (params?.value?.length >= 2) {
              onFilter({ field: chartConfig.xAxis, operator: "=", value: String(params.value[0]) });
            }
          }
        }}
      />
    );
  }

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading chart...</div>;
  }

  const option = buildSeriesOption(chartConfig, seriesData ?? []);

  return (
    <ReactECharts
      option={option}
      style={{ height: "100%", width: "100%" }}
      onEvents={{
        click: (params: any) => {
          const label = params?.name ?? params?.value?.[0];
          if (label != null) {
            onFilter({ field: chartConfig.xAxis, operator: "=", value: String(label) });
          }
        }
      }}
    />
  );
};

export function DashboardBuilder({ savedCharts }: { savedCharts: ChartConfig[] }) {
  const [dashboard, setDashboard] = useState<DashboardState>(() => {
    if (typeof window === "undefined") return defaultDashboard;
    try {
      const stored = localStorage.getItem(DASHBOARD_STORAGE_KEY);
      return stored ? (JSON.parse(stored) as DashboardState) : defaultDashboard;
    } catch {
      return defaultDashboard;
    }
  });

  useEffect(() => {
    localStorage.setItem(DASHBOARD_STORAGE_KEY, JSON.stringify(dashboard));
  }, [dashboard]);

  const addPanel = useCallback(
    (chartConfig?: ChartConfig, supersetUrl?: string) => {
      const id = `panel-${Date.now()}`;
      const nextPanel: DashboardPanel = {
        id,
        title: chartConfig ? chartConfig.title : "Superset Panel",
        chartConfig,
        supersetUrl
      };
      setDashboard(prev => ({
        ...prev,
        panels: [...prev.panels, nextPanel],
        layouts: [...prev.layouts, createPanelLayout(id, prev.layouts.length)]
      }));
    },
    []
  );

  const removePanel = useCallback((panelId: string) => {
    setDashboard(prev => ({
      ...prev,
      panels: prev.panels.filter(panel => panel.id !== panelId),
      layouts: prev.layouts.filter(layout => layout.i !== panelId)
    }));
  }, []);

  const handleLayoutChange = (layout: Layout[]) => {
    setDashboard(prev => ({ ...prev, layouts: layout }));
  };

  const handleFilter = (filter: DashboardFilter) => {
    setDashboard(prev => {
      const nextFilters = prev.filters.filter(existing => existing.field !== filter.field);
      nextFilters.push(filter);
      return { ...prev, filters: nextFilters };
    });
  };

  const clearFilters = () => {
    setDashboard(prev => ({ ...prev, filters: [] }));
  };

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(dashboard, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "biolink-dashboard.json";
    link.click();
    URL.revokeObjectURL(url);
  };

  const availableCharts = useMemo(() => {
    if (savedCharts.length > 0) return savedCharts;
    try {
      const stored = localStorage.getItem(SAVED_CHARTS_STORAGE_KEY);
      return stored ? (JSON.parse(stored) as ChartConfig[]) : [];
    } catch {
      return [];
    }
  }, [savedCharts]);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle>Dashboard Canvas</CardTitle>
            <p className="text-sm text-muted-foreground">
              Drag, resize, and link panels. Filters sync across all visuals and are stored locally.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Dialog>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Panel
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Add a panel</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label className="text-sm">From saved charts</Label>
                    <ScrollArea className="h-[260px] mt-2 rounded-md border">
                      <div className="p-3 space-y-2">
                        {availableCharts.length === 0 ? (
                          <div className="text-sm text-muted-foreground">No saved charts yet.</div>
                        ) : (
                          availableCharts.map((chart, index) => (
                            <button
                              key={`${chart.title}-${index}`}
                              className="w-full text-left p-2 rounded-md border hover:bg-accent"
                              onClick={() => addPanel(chart)}
                            >
                              <div className="text-sm font-medium">{chart.title}</div>
                              <div className="text-xs text-muted-foreground">
                                {chartTypeLabels[chart.type]} • {chart.xAxis}
                              </div>
                            </button>
                          ))
                        )}
                      </div>
                    </ScrollArea>
                  </div>
                  <div>
                    <Label className="text-sm">Or embed a Superset chart</Label>
                    <div className="flex gap-2 mt-2">
                      <Input placeholder="https://superset.example.com/superset/explore/...?" id="superset-panel-url" />
                      <Button
                        variant="outline"
                        onClick={() => {
                          const input = document.getElementById("superset-panel-url") as HTMLInputElement | null;
                          if (input?.value) {
                            addPanel(undefined, input.value);
                            input.value = "";
                          }
                        }}
                      >
                        Add
                      </Button>
                    </div>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
            <Button variant="outline" size="sm" onClick={exportJson}>
              <Download className="h-4 w-4 mr-2" />
              Export JSON
            </Button>
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <Filter className="h-4 w-4 mr-2" />
              Clear Filters
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {dashboard.filters.length === 0 ? (
            <Badge variant="outline">No active filters</Badge>
          ) : (
            dashboard.filters.map(filter => (
              <Badge key={`${filter.field}-${filter.value}`} variant="secondary">
                {filter.field} {filter.operator} {filter.value}
              </Badge>
            ))
          )}
        </CardContent>
      </Card>

      <ResponsiveGridLayout
        className="layout"
        layouts={{ lg: dashboard.layouts }}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480 }}
        cols={{ lg: 12, md: 8, sm: 4, xs: 2 }}
        rowHeight={30}
        onLayoutChange={layout => handleLayoutChange(layout)}
        draggableHandle=".drag-handle"
      >
        {dashboard.panels.map(panel => (
          <div key={panel.id} className="rounded-lg border bg-card shadow-sm flex flex-col">
            <div className="drag-handle cursor-move border-b px-3 py-2 flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">{panel.title}</div>
                {panel.chartConfig && (
                  <div className="text-xs text-muted-foreground">
                    {chartTypeLabels[panel.chartConfig.type]} • {panel.chartConfig.xAxis}
                  </div>
                )}
                {panel.supersetUrl && (
                  <div className="text-xs text-muted-foreground">Superset embed</div>
                )}
              </div>
              <Button variant="ghost" size="icon" onClick={() => removePanel(panel.id)}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 p-2">
              <PanelChart panel={panel} filters={dashboard.filters} onFilter={handleFilter} />
            </div>
          </div>
        ))}
      </ResponsiveGridLayout>
    </div>
  );
}
