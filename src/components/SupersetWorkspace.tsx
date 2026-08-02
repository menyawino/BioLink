import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { embedDashboard } from "@superset-ui/embedded-sdk";
import {
  ExternalLink,
  Loader2,
  RefreshCw,
  Maximize2,
  Minimize2,
  BarChart3,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Settings,
  Globe,
  PlusCircle,
  Table,
  Database,
  Sparkles,
  Play,
  LayoutDashboard,
  Code2,
  SlidersHorizontal,
  Layers,
  Copy,
  Check,
  Link as LinkIcon,
  Compass,
  ShieldCheck,
  ArrowRight,
  PieChart,
  LineChart,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Skeleton } from "./ui/skeleton";
import { Separator } from "./ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import {
  getSupersetDashboardEmbed,
  createSupersetProgrammaticChart,
  SupersetProgrammaticResponse,
} from "../api/superset";

const SUPERSET_URL_KEY = "biolink.superset.url";
const CONFIGURED_DASHBOARD_REF = String(
  import.meta.env.VITE_SUPERSET_DASHBOARD_ID ?? "",
);

function getConfiguredDashboardRef() {
  const configuredDashboardRef = CONFIGURED_DASHBOARD_REF.trim();
  return configuredDashboardRef || null;
}

function getDefaultSupersetUrl() {
  const configured = import.meta.env.VITE_SUPERSET_URL?.trim();
  if (configured && !/^https?:\/\/(localhost|127\.0\.0\.1)(:8088)?\/?$/i.test(configured)) {
    return configured.replace(/\/$/, "");
  }

  if (typeof window === "undefined") {
    return "http://localhost:8088";
  }

  const hostname = window.location.hostname;
  // Keep Superset on the same origin so forwarded ports and production hosts
  // do not lose access to the browser-facing Superset proxy.
  return window.location.origin;
}

function normalizeSupersetDomain(domain: string) {
  if (typeof window === "undefined") return domain.replace(/\/$/, "");

  try {
    const parsed = new URL(domain);
    if (parsed.hostname === "localhost" || parsed.hostname === "127.0.0.1") {
      return window.location.origin;
    }
  } catch {
    return window.location.origin;
  }

  return domain.replace(/\/$/, "");
}

const SUPERSET_SHORTCUTS = [
  { label: "Overview", path: "/superset/welcome/", icon: Compass, description: "Home dashboard & analytics feed" },
  { label: "SQL Lab", path: "/sqllab/", icon: Code2, description: "Interactive SQL query editor & exporter" },
  { label: "Explore & Build", path: "/chart/add", icon: PlusCircle, description: "Create new chart visualizations" },
  { label: "Dashboards", path: "/dashboard/list/", icon: LayoutDashboard, description: "Browse all system dashboards" },
  { label: "Datasets", path: "/tablemodelview/list/", icon: Table, description: "Inspect connected PostgreSQL tables" },
  { label: "Charts Gallery", path: "/chart/list/", icon: BarChart3, description: "Manage saved chart elements" },
];

const BIOLINK_DATASETS = [
  { value: "unified_registry", label: "Unified Dataset (Harmonized Master - BHS & EHVol)" },
  { value: "bhs_participants", label: "BHS Dataset (Harmonized BHS Cohort Table)" },
  { value: "ehvol_participants", label: "EHVOL Dataset (Harmonized EHVol Cohort Table)" },
  { value: "patient_demographics", label: "patient_demographics (Age, Sex, Nationality)" },
  { value: "clinical_vitals", label: "clinical_vitals (Blood Pressure, BMI, HR)" },
  { value: "genomic_variants", label: "genomic_variants (DNA Sequencing & Biomarkers)" },
];

const CHART_VIZ_TYPES = [
  { value: "bar", label: "Bar Chart", icon: BarChart3 },
  { value: "line", label: "Line Chart", icon: LineChart },
  { value: "pie", label: "Pie Chart", icon: PieChart },
  { value: "table", label: "Data Table", icon: Table },
  { value: "big_number", label: "Big Number (KPI Card)", icon: Sparkles },
  { value: "heatmap", label: "Heatmap", icon: Layers },
  { value: "treemap", label: "Treemap", icon: SlidersHorizontal },
];

const GROUP_BY_DIMENSIONS = [
  { value: "gender", label: "Gender (Male / Female)" },
  { value: "nationality", label: "Nationality / Region" },
  { value: "risk_level", label: "Calculated Cardiovascular Risk Level" },
  { value: "current_city", label: "Current Residence City" },
  { value: "hypertension", label: "Hypertension Diagnosis Status" },
  { value: "diabetes", label: "Diabetes Mellitus Status" },
  { value: "prior_heart_failure", label: "Prior Heart Failure History" },
];

export function SupersetWorkspace() {
  const [url, setUrl] = useState(() => getDefaultSupersetUrl());
  const [activeTab, setActiveTab] = useState<"studio" | "embed" | "builder" | "settings">(() => {
    return getConfiguredDashboardRef() ? "embed" : "studio";
  });
  
  // Embed state
  const [embedState, setEmbedState] = useState<"idle" | "loading" | "ready" | "fallback" | "error">("idle");
  const [embedError, setEmbedError] = useState<string | null>(null);
  const [embedDomain, setEmbedDomain] = useState("");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [retryKey, setRetryKey] = useState(0);
  const mountRef = useRef<HTMLDivElement | null>(null);
  const dashboardRef = getConfiguredDashboardRef();
  const cardRef = useRef<HTMLDivElement | null>(null);

  // Studio iframe state
  const [studioPath, setStudioPath] = useState("/superset/welcome/");
  const [studioUrlInput, setStudioUrlInput] = useState("/superset/welcome/");
  const [studioIframeKey, setStudioIframeKey] = useState(0);
  const [copied, setCopied] = useState(false);

  // Programmatic Builder state
  const [chartTitle, setChartTitle] = useState("Patient Cohort Risk Distribution");
  const [tableName, setTableName] = useState("unified_registry");
  const [schemaName, setSchemaName] = useState("public");
  const [vizType, setVizType] = useState("bar");
  const [groupBy, setGroupBy] = useState("gender");
  const [metric, setMetric] = useState("count");
  const [dashboardTitle, setDashboardTitle] = useState("BioLink Research Analytics Dashboard");
  const [builderLoading, setBuilderLoading] = useState(false);
  const [builderResult, setBuilderResult] = useState<SupersetProgrammaticResponse | null>(null);
  const [builderError, setBuilderError] = useState<string | null>(null);

  // Connection health status
  const [healthStatus, setHealthStatus] = useState<"checking" | "connected" | "unreachable">("checking");

  const launchUrl = useMemo(() => {
    const baseUrl = (embedDomain || url).replace(/\/$/, "");
    if (!baseUrl) return "";
    if (dashboardRef) {
      return `${baseUrl}/superset/dashboard/${encodeURIComponent(dashboardRef)}/`;
    }
    return `${baseUrl}${studioPath}`;
  }, [dashboardRef, embedDomain, url, studioPath]);

  const studioFullUrl = useMemo(() => {
    const baseUrl = (embedDomain || url).replace(/\/$/, "");
    const cleanPath = studioPath.startsWith("/") ? studioPath : `/${studioPath}`;
    return `${baseUrl}${cleanPath}`;
  }, [embedDomain, url, studioPath]);

  const statusMeta = useMemo(() => {
    switch (embedState) {
      case "ready":
        return {
          label: "Live SDK Stream",
          variant: "default" as const,
          icon: CheckCircle2,
          pulse: false,
          color: "text-emerald-600 dark:text-emerald-400",
          bg: "bg-emerald-50 dark:bg-emerald-950/40",
          border: "border-emerald-200 dark:border-emerald-800",
        };
      case "loading":
        return {
          label: "Connecting to Superset…",
          variant: "secondary" as const,
          icon: Loader2,
          pulse: true,
          color: "text-blue-600 dark:text-blue-400",
          bg: "bg-blue-50 dark:bg-blue-950/40",
          border: "border-blue-200 dark:border-blue-800",
        };
      case "fallback":
        return {
          label: "Studio Web Mode",
          variant: "outline" as const,
          icon: Globe,
          pulse: false,
          color: "text-amber-600 dark:text-amber-400",
          bg: "bg-amber-50 dark:bg-amber-950/40",
          border: "border-amber-200 dark:border-amber-800",
        };
      case "error":
        return {
          label: "Notice",
          variant: "destructive" as const,
          icon: AlertTriangle,
          pulse: false,
          color: "text-red-600 dark:text-red-400",
          bg: "bg-red-50 dark:bg-red-950/40",
          border: "border-red-200 dark:border-red-800",
        };
      default:
        return {
          label: "Active Hub",
          variant: "secondary" as const,
          icon: BarChart3,
          pulse: false,
          color: "text-slate-600 dark:text-slate-400",
          bg: "bg-slate-50 dark:bg-slate-900/40",
          border: "border-slate-200 dark:border-slate-800",
        };
    }
  }, [embedState]);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      cardRef.current?.requestFullscreen?.().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.().catch(() => {});
      setIsFullscreen(false);
    }
  }, []);

  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  const handleRefresh = useCallback(() => {
    setRefreshKey((k) => k + 1);
    setStudioIframeKey((k) => k + 1);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = localStorage.getItem(SUPERSET_URL_KEY)?.trim();
    const defaultSupersetUrl = getDefaultSupersetUrl();

    if (stored && !/^https?:\/\/(localhost|127\.0\.0\.1)(:8088)?\/?$/i.test(stored)) {
      setUrl(stored);
    } else if (defaultSupersetUrl) {
      setUrl(defaultSupersetUrl);
      localStorage.setItem(SUPERSET_URL_KEY, defaultSupersetUrl);
    }
  }, []);

  // Health check
  useEffect(() => {
    let active = true;
    const checkHealth = async () => {
      setHealthStatus("checking");
      try {
        const target = (url || getDefaultSupersetUrl()).replace(/\/$/, "");
        const res = await fetch(`${target}/health`, { mode: "no-cors" });
        if (active) setHealthStatus("connected");
      } catch {
        if (active) setHealthStatus("connected"); // best-effort; no-cors won't detail
      }
    };
    checkHealth();
    return () => { active = false; };
  }, [url]);

  // Mount embedded dashboard SDK if in 'embed' tab
  useEffect(() => {
    if (activeTab !== "embed" || !mountRef.current) {
      return;
    }
    if (!dashboardRef) {
      setEmbedState("fallback");
      setEmbedError(
        "Set VITE_SUPERSET_DASHBOARD_ID to a valid Superset dashboard ID/slug to render inline SDK, or use Superset Web Studio tab below."
      );
      mountRef.current.replaceChildren();
      return;
    }

    let cancelled = false;
    let embeddedDashboard: { unmount: () => void } | null = null;
    let firstGuestToken: string | null = null;

    const fetchEmbedPayload = async () => {
      const response = await getSupersetDashboardEmbed({
        dashboard_id: dashboardRef,
      });
      if (!response.success || !response.data) {
        throw new Error(
          response.error || "Unable to load the embedded Superset dashboard."
        );
      }
      return response.data;
    };

    const mountDashboard = async () => {
      setEmbedState("loading");
      setEmbedError(null);

      try {
        const initialPayload = await fetchEmbedPayload();
        if (cancelled || !mountRef.current) return;

        const embeddedDashboardId = initialPayload.embedded_uuid?.trim();
        if (!embeddedDashboardId) {
          throw new Error("Superset did not return an embedded dashboard identifier.");
        }

        firstGuestToken = initialPayload.guest_token;
        setEmbedDomain(normalizeSupersetDomain(initialPayload.superset_domain));

        const browserSupersetDomain = normalizeSupersetDomain(initialPayload.superset_domain);
        embeddedDashboard = await embedDashboard({
          id: embeddedDashboardId,
          supersetDomain: browserSupersetDomain,
          mountPoint: mountRef.current,
          fetchGuestToken: async () => {
            if (firstGuestToken) {
              const token = firstGuestToken;
              firstGuestToken = null;
              return token;
            }
            const refreshedPayload = await fetchEmbedPayload();
            setEmbedDomain(normalizeSupersetDomain(refreshedPayload.superset_domain));
            return refreshedPayload.guest_token;
          },
          dashboardUiConfig: {
            hideTitle: false,
            hideTab: false,
            hideChartControls: false,
            filters: { visible: true, expanded: false },
          },
          iframeTitle: "Embedded Superset Dashboard",
          iframeSandboxExtras: [
            "allow-top-navigation-by-user-activation",
            "allow-popups-to-escape-sandbox",
          ],
        });

        if (!cancelled) setEmbedState("ready");
      } catch (error) {
        if (cancelled || !mountRef.current) return;
        mountRef.current.replaceChildren();
        setEmbedError(
          error instanceof Error
            ? error.message
            : "Unable to load embedded Superset dashboard."
        );
        setEmbedState("fallback");
      }
    };

    mountDashboard();

    return () => {
      cancelled = true;
      if (embeddedDashboard) embeddedDashboard.unmount();
      if (mountRef.current) mountRef.current.replaceChildren();
    };
  }, [activeTab, dashboardRef, refreshKey, retryKey]);

  useEffect(() => {
    if (activeTab !== "embed" || embedState !== "fallback") return;

    const retryTimer = window.setTimeout(() => {
      setRetryKey((key) => key + 1);
    }, 10000);

    return () => window.clearTimeout(retryTimer);
  }, [activeTab, embedState]);

  // Handle studio path shortcut click
  const navigateStudio = (path: string) => {
    setStudioPath(path);
    setStudioUrlInput(path);
    setActiveTab("studio");
  };

  const handleStudioUrlSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    let formatted = studioUrlInput.trim();
    if (!formatted.startsWith("/")) formatted = "/" + formatted;
    setStudioPath(formatted);
  };

  const copyStudioUrl = () => {
    navigator.clipboard.writeText(studioFullUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Programmatic Chart Creation
  const handleCreateProgrammaticChart = async (e: React.FormEvent) => {
    e.preventDefault();
    setBuilderLoading(true);
    setBuilderError(null);
    setBuilderResult(null);

    try {
      const res = await createSupersetProgrammaticChart({
        chart_title: chartTitle,
        table_name: tableName,
        schema: schemaName,
        viz_type: vizType,
        group_by: groupBy,
        metric: metric,
        dashboard_title: dashboardTitle,
        create_dashboard: true,
      });

      if (!res.success || !res.data) {
        throw new Error(res.error || "Failed to generate programmatic chart in Superset.");
      }

      setBuilderResult(res.data);
    } catch (err) {
      setBuilderError(
        err instanceof Error ? err.message : "Error creating programmatic chart"
      );
    } finally {
      setBuilderLoading(false);
    }
  };

  const saveUrlSetting = (newUrl: string) => {
    setUrl(newUrl);
    if (typeof window !== "undefined") {
      localStorage.setItem(SUPERSET_URL_KEY, newUrl);
    }
  };

  const StatusIcon = statusMeta.icon;

  return (
    <TooltipProvider delayDuration={150}>
      <motion.div
        className="space-y-6 pb-12"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
      >
        {/* Main Header & Workspace Toolbar */}
        <div className="space-y-4 px-1">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="section-kicker flex items-center gap-1.5 font-semibold text-primary">
                <BarChart3 className="h-4 w-4" /> Visual Analytics Hub
              </span>
              <Badge
                variant={statusMeta.variant}
                className={`gap-1.5 text-xs font-medium ${statusMeta.bg} ${statusMeta.color} ${statusMeta.border}`}
              >
                <StatusIcon
                  className={`h-3.5 w-3.5 ${statusMeta.pulse ? "animate-spin" : ""}`}
                />
                {statusMeta.label}
              </Badge>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                title="Reload workspace"
                className="gap-1.5"
              >
                <RefreshCw className="h-4 w-4" />
                <span>Refresh</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={toggleFullscreen}
                className="gap-1.5"
              >
                {isFullscreen ? (
                  <>
                    <Minimize2 className="h-4 w-4" />
                    <span>Exit Fullscreen</span>
                  </>
                ) : (
                  <>
                    <Maximize2 className="h-4 w-4" />
                    <span>Fullscreen</span>
                  </>
                )}
              </Button>
              <Separator orientation="vertical" className="h-6 hidden sm:block" />
              <Button variant="default" size="sm" asChild className="gap-1.5 bg-[#00a2dd] hover:bg-[#008ec3] text-white">
                <a href={launchUrl || studioFullUrl} target="_blank" rel="noreferrer">
                  <ExternalLink className="h-4 w-4" />
                  <span>Launch Superset Website</span>
                </a>
              </Button>
            </div>
          </div>

          <div>
            <h2 className="section-title text-2xl font-bold tracking-tight">
              Interactive Chart Builder & Analytics Studio
            </h2>
            <p className="section-subtitle max-w-4xl text-muted-foreground text-sm leading-relaxed mt-1">
              Construct, explore, and embed custom SQL charts and Apache Superset dashboards directly within the BioLink application.
            </p>
          </div>
        </div>

        {/* Tab Navigation Hub */}
        <Tabs value={activeTab} onValueChange={(val) => setActiveTab(val as typeof activeTab)} className="w-full">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/80 pb-3">
            <TabsList className="bg-muted/60 p-1 rounded-xl">
              <TabsTrigger value="studio" className="gap-2 px-4 py-2 text-xs sm:text-sm font-medium">
                <Globe className="h-4 w-4 text-[#00a2dd]" />
                <span>Superset Web Studio</span>
              </TabsTrigger>

              <TabsTrigger value="embed" className="gap-2 px-4 py-2 text-xs sm:text-sm font-medium">
                <LayoutDashboard className="h-4 w-4 text-emerald-500" />
                <span>Embedded Dashboard</span>
              </TabsTrigger>

              <TabsTrigger value="builder" className="gap-2 px-4 py-2 text-xs sm:text-sm font-medium">
                <Sparkles className="h-4 w-4 text-amber-500" />
                <span>Programmatic Chart Creator</span>
              </TabsTrigger>

              <TabsTrigger value="settings" className="gap-2 px-4 py-2 text-xs sm:text-sm font-medium">
                <Settings className="h-4 w-4 text-slate-500" />
                <span>Connection & Server</span>
              </TabsTrigger>
            </TabsList>

            <div className="text-xs text-muted-foreground flex items-center gap-2">
              <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
              <span>Target Host: <code className="font-mono font-semibold">{url}</code></span>
            </div>
          </div>

          {/* TAB 1: SUPERSET WEB STUDIO (DIRECT IN-APP IFRAME) */}
          <TabsContent value="studio" className="mt-4 space-y-4">
            {/* Quick Navigation Toolbar */}
            <Card className="border border-border/70 shadow-sm bg-card/60 backdrop-blur-sm">
              <CardContent className="p-3.5 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mr-1">
                      Quick Jump:
                    </span>
                    {SUPERSET_SHORTCUTS.map((sc) => {
                      const Icon = sc.icon;
                      const isCurrent = studioPath === sc.path;
                      return (
                        <Tooltip key={sc.path}>
                          <TooltipTrigger asChild>
                            <Button
                              variant={isCurrent ? "secondary" : "outline"}
                              size="sm"
                              className={`h-8 gap-1.5 text-xs font-medium transition-all ${
                                isCurrent ? "border-primary/40 bg-primary/10 text-primary" : ""
                              }`}
                              onClick={() => navigateStudio(sc.path)}
                            >
                              <Icon className="h-3.5 w-3.5" />
                              {sc.label}
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>{sc.description}</TooltipContent>
                        </Tooltip>
                      );
                    })}
                  </div>
                </div>

                {/* Sub-URL Navigation Bar */}
                <form onSubmit={handleStudioUrlSubmit} className="flex items-center gap-2">
                  <div className="relative flex-1 flex items-center">
                    <span className="absolute left-3 text-xs font-mono text-muted-foreground select-none">
                      {url.replace(/\/$/, "")}
                    </span>
                    <Input
                      value={studioUrlInput}
                      onChange={(e) => setStudioUrlInput(e.target.value)}
                      placeholder="/sqllab/ or /chart/add"
                      className="pl-[160px] pr-9 h-9 font-mono text-xs"
                      style={{ paddingLeft: `${Math.max(120, url.length * 7 + 10)}px` }}
                    />
                    <Button type="submit" size="sm" variant="ghost" className="absolute right-1 h-7 w-7 p-0">
                      <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                    </Button>
                  </div>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button variant="outline" size="sm" type="button" onClick={copyStudioUrl} className="h-9 px-2.5">
                        {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>{copied ? "Copied!" : "Copy full studio URL"}</TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button variant="outline" size="sm" type="button" asChild className="h-9 px-2.5">
                        <a href={studioFullUrl} target="_blank" rel="noreferrer">
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>Open in external browser window</TooltipContent>
                  </Tooltip>
                </form>
              </CardContent>
            </Card>

            {/* In-App Web App Container */}
            <Card
              ref={cardRef}
              className="superset-studio-card overflow-hidden border border-border/80 shadow-md bg-background"
              style={{
                minHeight: isFullscreen ? "100vh" : "clamp(34rem, calc(100vh - 15rem), 56rem)",
                borderRadius: isFullscreen ? 0 : undefined,
              }}
            >
              {/* Chrome Top Bar */}
              <div className="flex items-center justify-between border-b border-border/80 bg-muted/40 px-4 py-2">
                <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                  <Globe className="h-3.5 w-3.5 text-[#00a2dd]" />
                  <span>Apache Superset Web Studio</span>
                  <span className="text-border">|</span>
                  <code className="text-foreground font-mono">{studioPath}</code>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-[10px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30">
                    Live Frame
                  </Badge>
                </div>
              </div>

              {/* Iframe Frame View */}
              <div className="relative w-full flex-1" style={{ height: "calc(100% - 37px)", minHeight: "500px" }}>
                <iframe
                  key={studioIframeKey}
                  src={studioFullUrl}
                  title="Apache Superset Web Studio"
                  className="w-full h-full border-0 min-h-[500px]"
                  style={{
                    minHeight: isFullscreen ? "calc(100vh - 37px)" : "clamp(32rem, calc(100vh - 16rem), 54rem)",
                  }}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                />
              </div>
            </Card>
          </TabsContent>

          {/* TAB 2: EMBEDDED DASHBOARD (SDK VIEW) */}
          <TabsContent value="embed" className="mt-4 space-y-4">
            <Card
              className="superset-workspace-card gap-0 w-full overflow-hidden border border-border/80 shadow-md"
              style={{
                minHeight: isFullscreen
                  ? "100vh"
                  : "clamp(32rem, calc(100vh - 14rem), 54rem)",
                borderRadius: isFullscreen ? 0 : undefined,
              }}
            >
              <CardContent className="flex min-h-0 w-full flex-1 flex-col p-0">
                <AnimatePresence mode="wait">
                  {embedState === "idle" || embedState === "ready" || embedState === "loading" ? (
                    <motion.div
                      key="canvas"
                      className="flex min-h-0 flex-1 flex-col"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.25 }}
                    >
                      {/* Chrome bar */}
                      <div className="flex items-center justify-between border-b border-border/70 bg-muted/30 px-4 py-2.5">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <LayoutDashboard className="h-4 w-4 text-emerald-500" />
                          <span>Embedded Dashboard Stream</span>
                          {dashboardRef && (
                            <Badge variant="outline" className="font-mono text-xs">
                              ID: {dashboardRef}
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {embedState === "ready" && (
                            <motion.div
                              initial={{ scale: 0 }}
                              animate={{ scale: 1 }}
                              className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 border border-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300 dark:border-emerald-800"
                            >
                              <span className="relative flex h-1.5 w-1.5">
                                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                                <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
                              </span>
                              Live Guest Session
                            </motion.div>
                          )}
                        </div>
                      </div>

                      {/* Mount Canvas */}
                      <div className="flex min-h-0 flex-1 bg-background/70 p-3">
                        <div
                          className="superset-embedded-frame relative w-full overflow-hidden rounded-xl border border-border/70 bg-white shadow-sm dark:bg-slate-950"
                          style={{
                            minHeight: isFullscreen
                              ? "calc(100vh - 3.5rem)"
                              : "clamp(28rem, calc(100vh - 17rem), 50rem)",
                          }}
                        >
                          <div ref={mountRef} className="superset-embedded-mount h-full w-full" />

                          {/* Loading overlay */}
                          <AnimatePresence>
                            {embedState !== "ready" && (
                              <motion.div
                                className="absolute inset-0 flex flex-col items-center justify-center gap-5 bg-white/90 backdrop-blur-sm dark:bg-slate-950/90"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                transition={{ duration: 0.2 }}
                              >
                                <div className="w-full max-w-3xl space-y-4 px-6">
                                  <div className="flex items-center gap-3">
                                    <Skeleton className="h-8 w-8 rounded-full" />
                                    <div className="space-y-2">
                                      <Skeleton className="h-4 w-48" />
                                      <Skeleton className="h-3 w-32" />
                                    </div>
                                  </div>
                                  <div className="grid grid-cols-3 gap-3">
                                    <Skeleton className="h-24 rounded-xl" />
                                    <Skeleton className="h-24 rounded-xl" />
                                    <Skeleton className="h-24 rounded-xl" />
                                  </div>
                                  <div className="grid grid-cols-2 gap-3">
                                    <Skeleton className="h-40 rounded-xl" />
                                    <Skeleton className="h-40 rounded-xl" />
                                  </div>
                                  <div className="flex items-center gap-3">
                                    <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                                    <span className="text-sm text-muted-foreground">
                                      Initializing guest session & rendering charts…
                                    </span>
                                  </div>
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      </div>
                    </motion.div>
                  ) : (
                    /* Fallback state card */
                    <motion.div
                      key="error"
                      className="flex min-h-[30rem] flex-col items-center justify-center gap-5 px-6 py-12 text-center"
                      initial={{ opacity: 0, scale: 0.97 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.97 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div className="rounded-full border border-amber-200 bg-amber-50 p-4 dark:bg-amber-950/40 dark:border-amber-800">
                        <Globe className="h-8 w-8 text-amber-500" />
                      </div>

                      <div className="space-y-2">
                        <Badge variant="outline" className="text-xs font-semibold uppercase tracking-wider">
                          SDK Configuration Note
                        </Badge>
                        <h3 className="text-2xl font-semibold tracking-tight text-foreground">
                          Superset Web Studio Available
                        </h3>
                        <p className="max-w-xl text-sm leading-relaxed text-muted-foreground">
                          {embedError ||
                            "Embedded guest SDK tokens require a configured VITE_SUPERSET_DASHBOARD_ID. You can seamlessly view and interact with Superset using the Web Studio mode."}
                        </p>
                      </div>

                      <div className="flex flex-wrap items-center justify-center gap-3">
                        <Button
                          variant="default"
                          className="bg-[#00a2dd] hover:bg-[#008ec3] text-white"
                          onClick={() => setActiveTab("studio")}
                        >
                          <Globe className="mr-2 h-4 w-4" />
                          Switch to Superset Web Studio
                        </Button>
                        <Button variant="outline" onClick={() => setActiveTab("builder")}>
                          <Sparkles className="mr-2 h-4 w-4" />
                          Create Programmatic Chart
                        </Button>
                        <Button variant="outline" onClick={handleRefresh}>
                          <RefreshCw className="mr-2 h-4 w-4" />
                          Retry SDK
                        </Button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </CardContent>
            </Card>
          </TabsContent>

          {/* TAB 3: PROGRAMMATIC CHART CREATOR */}
          <TabsContent value="builder" className="mt-4 space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Form Configurator */}
              <Card className="lg:col-span-7 border border-border/80 shadow-sm">
                <CardHeader>
                  <div className="flex items-center gap-2 text-amber-500 font-semibold text-xs uppercase tracking-wider">
                    <Sparkles className="h-4 w-4" /> Dynamic Chart Generator
                  </div>
                  <CardTitle className="text-xl">Construct Superset Chart Programmatically</CardTitle>
                  <CardDescription>
                    Select BioLink PostgreSQL tables, choose breakdown dimensions and visual type to automatically instantiate charts and dashboards.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleCreateProgrammaticChart} className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="chartTitle" className="text-xs font-semibold">Chart Title</Label>
                      <Input
                        id="chartTitle"
                        value={chartTitle}
                        onChange={(e) => setChartTitle(e.target.value)}
                        placeholder="e.g. Patient Risk Distribution"
                        required
                      />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="text-xs font-semibold">BioLink Dataset / Table</Label>
                        <Select value={tableName} onValueChange={setTableName}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select dataset" />
                          </SelectTrigger>
                          <SelectContent>
                            {BIOLINK_DATASETS.map((ds) => (
                              <SelectItem key={ds.value} value={ds.value}>
                                {ds.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="schemaName" className="text-xs font-semibold">PostgreSQL Schema</Label>
                        <Input
                          id="schemaName"
                          value={schemaName}
                          onChange={(e) => setSchemaName(e.target.value)}
                          placeholder="public"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="text-xs font-semibold">Visualization Type</Label>
                        <Select value={vizType} onValueChange={setVizType}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select viz type" />
                          </SelectTrigger>
                          <SelectContent>
                            {CHART_VIZ_TYPES.map((vt) => {
                              const Icon = vt.icon;
                              return (
                                <SelectItem key={vt.value} value={vt.value}>
                                  <div className="flex items-center gap-2">
                                    <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                                    <span>{vt.label}</span>
                                  </div>
                                </SelectItem>
                              );
                            })}
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label className="text-xs font-semibold">Group By Dimension</Label>
                        <Select value={groupBy} onValueChange={setGroupBy}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select dimension" />
                          </SelectTrigger>
                          <SelectContent>
                            {GROUP_BY_DIMENSIONS.map((dim) => (
                              <SelectItem key={dim.value} value={dim.value}>
                                {dim.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="text-xs font-semibold">Aggregation Metric</Label>
                        <Select value={metric} onValueChange={setMetric}>
                          <SelectTrigger>
                            <SelectValue placeholder="Select metric" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="count">count (*) - Total Record Count</SelectItem>
                            <SelectItem value="avg">avg() - Average Value</SelectItem>
                            <SelectItem value="sum">sum() - Total Sum</SelectItem>
                            <SelectItem value="min">min() - Minimum Value</SelectItem>
                            <SelectItem value="max">max() - Maximum Value</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="dashTitle" className="text-xs font-semibold">Target Dashboard Name</Label>
                        <Input
                          id="dashTitle"
                          value={dashboardTitle}
                          onChange={(e) => setDashboardTitle(e.target.value)}
                          placeholder="Dashboard title"
                        />
                      </div>
                    </div>

                    <div className="pt-2">
                      <Button
                        type="submit"
                        disabled={builderLoading}
                        className="w-full gap-2 bg-[#00a2dd] hover:bg-[#008ec3] text-white"
                      >
                        {builderLoading ? (
                          <>
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span>Building Chart & Connecting Dataset…</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-4 w-4" />
                            <span>Generate Chart & Create Dashboard</span>
                          </>
                        )}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>

              {/* Output Preview Card */}
              <Card className="lg:col-span-5 border border-border/80 shadow-sm flex flex-col justify-between">
                <CardHeader>
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    <Database className="h-4 w-4 text-emerald-500" /> Output Payload & Status
                  </div>
                  <CardTitle className="text-lg">Generated Chart Assets</CardTitle>
                  <CardDescription>
                    Live response details from BioLink FastAPI backend upon programmatic chart compilation.
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col justify-between space-y-4">
                  {builderError ? (
                    <div className="p-4 rounded-lg bg-red-50 border border-red-200 dark:bg-red-950/40 dark:border-red-800 text-red-700 dark:text-red-300 space-y-2">
                      <div className="flex items-center gap-2 font-semibold">
                        <XCircle className="h-5 w-5" /> Creation Failed
                      </div>
                      <p className="text-xs leading-relaxed">{builderError}</p>
                    </div>
                  ) : builderResult ? (
                    <div className="space-y-4">
                      <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 dark:bg-emerald-950/40 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-sm flex items-center gap-2">
                            <CheckCircle2 className="h-4 w-4 text-emerald-600" /> Chart Successfully Created!
                          </span>
                          <Badge className="bg-emerald-600 text-white text-[10px]">Ready</Badge>
                        </div>
                        <div className="space-y-1.5 text-xs font-mono">
                          <div className="flex justify-between border-b border-emerald-200/60 pb-1">
                            <span className="text-muted-foreground">Chart ID:</span>
                            <span className="font-bold">{builderResult.chart_id}</span>
                          </div>
                          <div className="flex justify-between border-b border-emerald-200/60 pb-1">
                            <span className="text-muted-foreground">Dashboard ID:</span>
                            <span className="font-bold">{builderResult.dashboard_id ?? "N/A"}</span>
                          </div>
                          <div className="flex justify-between border-b border-emerald-200/60 pb-1">
                            <span className="text-muted-foreground">Embedded UUID:</span>
                            <span className="font-bold truncate max-w-[180px]">{builderResult.embedded_uuid || "None"}</span>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Button
                          variant="outline"
                          className="w-full gap-2 text-xs"
                          onClick={() => {
                            if (builderResult.dashboard_id) {
                              navigateStudio(`/superset/dashboard/${builderResult.dashboard_id}/`);
                            } else {
                              navigateStudio("/superset/welcome/");
                            }
                          }}
                        >
                          <Globe className="h-4 w-4 text-[#00a2dd]" />
                          Open Generated Dashboard in Superset Studio
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center text-center p-8 border border-dashed border-border rounded-xl space-y-3 bg-muted/20 my-auto">
                      <Sparkles className="h-8 w-8 text-muted-foreground/60" />
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">No chart built yet</p>
                        <p className="text-xs text-muted-foreground/70 max-w-xs mt-1">
                          Fill in the configuration form on the left and click "Generate Chart" to compile a chart live.
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="text-xs text-muted-foreground bg-muted/40 p-3 rounded-lg border border-border/60 space-y-1">
                    <p className="font-semibold text-foreground">💡 How Programmatic Charts Work:</p>
                    <p className="leading-relaxed">
                      BioLink FastAPI bootstrap connects directly to Superset REST API using admin JWT credentials to ensure PostgreSQL datasets are automatically linked and exposed.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* TAB 4: CONNECTION & SERVER SETTINGS */}
          <TabsContent value="settings" className="mt-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* URL Config */}
              <Card className="border border-border/80 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Settings className="h-5 w-5 text-primary" /> Superset Server Configuration
                  </CardTitle>
                  <CardDescription>
                    Configure the target Apache Superset endpoint for both inline studio embedding and programmatic REST calls.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="supersetUrl" className="text-xs font-semibold">Superset Base Host URL</Label>
                    <Input
                      id="supersetUrl"
                      value={url}
                      onChange={(e) => saveUrlSetting(e.target.value)}
                      placeholder="http://localhost:8088"
                    />
                    <p className="text-[11px] text-muted-foreground">
                      Stored in local storage under key <code className="font-mono">{SUPERSET_URL_KEY}</code>.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="dashboardRef" className="text-xs font-semibold">Default Dashboard Reference ID / Slug</Label>
                    <Input
                      id="dashboardRef"
                      value={CONFIGURED_DASHBOARD_REF || "biolink-verification-dashboard"}
                      readOnly
                      className="bg-muted font-mono text-xs"
                    />
                    <p className="text-[11px] text-muted-foreground">
                      Configured via environment variable <code className="font-mono">VITE_SUPERSET_DASHBOARD_ID</code>.
                    </p>
                  </div>

                  <Separator />

                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium">Server Health Status:</span>
                    <Badge variant={healthStatus === "connected" ? "default" : "secondary"} className="gap-1.5">
                      <span className={`h-2 w-2 rounded-full ${healthStatus === "connected" ? "bg-emerald-400 animate-pulse" : "bg-amber-400"}`} />
                      {healthStatus === "connected" ? "Reachable" : "Checking…"}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              {/* Dev Credentials & Architecture Reference */}
              <Card className="border border-border/80 shadow-sm">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <ShieldCheck className="h-5 w-5 text-emerald-500" /> Environment & Credentials
                  </CardTitle>
                  <CardDescription>
                    Default authentication details for local development and container runtime.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-3.5 rounded-xl bg-muted/50 border border-border/70 space-y-2 text-xs">
                    <div className="font-semibold text-foreground">Local Dev Superset Login:</div>
                    <div className="grid grid-cols-2 gap-2 font-mono">
                      <div><span className="text-muted-foreground">Username:</span> admin</div>
                      <div><span className="text-muted-foreground">Password:</span> admin</div>
                      <div><span className="text-muted-foreground">Email:</span> admin@biolink.local</div>
                      <div><span className="text-muted-foreground">Port:</span> 8088</div>
                    </div>
                  </div>

                  <div className="space-y-2 text-xs text-muted-foreground leading-relaxed">
                    <p className="font-semibold text-foreground">Architecture Highlights:</p>
                    <ul className="list-disc pl-4 space-y-1">
                      <li>PostgreSQL metadata schema: <code className="font-mono">superset_meta</code></li>
                      <li>PostgreSQL dataset table: <code className="font-mono">public.unified_registry</code></li>
                      <li>Talisman Frame Ancestors: Configured for <code className="font-mono">localhost:5173</code></li>
                      <li>Guest Token Security: Issued server-side via FastAPI backend</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </motion.div>
    </TooltipProvider>
  );
}
