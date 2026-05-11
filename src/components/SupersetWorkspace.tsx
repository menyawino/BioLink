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
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Skeleton } from "./ui/skeleton";
import { Separator } from "./ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import { getSupersetDashboardEmbed } from "../api/superset";

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
  if (configured) {
    return configured;
  }

  if (typeof window === "undefined") {
    return "";
  }

  const hostname = window.location.hostname;
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    const url = new URL(window.location.origin);
    url.port = "8088";
    return url.toString().replace(/\/$/, "");
  }

  return "";
}

export function SupersetWorkspace() {
  const [url, setUrl] = useState(() => getDefaultSupersetUrl());
  const [embedState, setEmbedState] = useState<
    "idle" | "loading" | "ready" | "fallback" | "error"
  >("idle");
  const [embedError, setEmbedError] = useState<string | null>(null);
  const [embedDomain, setEmbedDomain] = useState("");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const mountRef = useRef<HTMLDivElement | null>(null);
  const dashboardRef = getConfiguredDashboardRef();
  const cardRef = useRef<HTMLDivElement | null>(null);

  const launchUrl = useMemo(() => {
    const baseUrl = (embedDomain || url).replace(/\/$/, "");
    if (!baseUrl) {
      return "";
    }
    if (dashboardRef) {
      return `${baseUrl}/superset/dashboard/${encodeURIComponent(dashboardRef)}/`;
    }
    return `${baseUrl}/superset/welcome/`;
  }, [dashboardRef, embedDomain, url]);

  const statusMeta = useMemo(() => {
    switch (embedState) {
      case "ready":
        return {
          label: "Live",
          variant: "default" as const,
          icon: CheckCircle2,
          pulse: false,
          color: "text-emerald-600",
          bg: "bg-emerald-50",
          border: "border-emerald-200",
        };
      case "loading":
        return {
          label: "Connecting…",
          variant: "secondary" as const,
          icon: Loader2,
          pulse: true,
          color: "text-blue-600",
          bg: "bg-blue-50",
          border: "border-blue-200",
        };
      case "fallback":
        return {
          label: "Fallback mode",
          variant: "outline" as const,
          icon: AlertTriangle,
          pulse: false,
          color: "text-amber-600",
          bg: "bg-amber-50",
          border: "border-amber-200",
        };
      case "error":
        return {
          label: "Error",
          variant: "destructive" as const,
          icon: XCircle,
          pulse: false,
          color: "text-red-600",
          bg: "bg-red-50",
          border: "border-red-200",
        };
      default:
        return {
          label: "Idle",
          variant: "secondary" as const,
          icon: BarChart3,
          pulse: false,
          color: "text-slate-600",
          bg: "bg-slate-50",
          border: "border-slate-200",
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
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = localStorage.getItem(SUPERSET_URL_KEY)?.trim();
    const defaultSupersetUrl = getDefaultSupersetUrl();

    if (stored) {
      setUrl(stored);
    } else if (defaultSupersetUrl) {
      setUrl(defaultSupersetUrl);
      localStorage.setItem(SUPERSET_URL_KEY, defaultSupersetUrl);
    } else {
      setUrl("");
    }
  }, []);

  useEffect(() => {
    if (!mountRef.current) {
      return;
    }
    if (!dashboardRef) {
      setEmbedState(launchUrl ? "fallback" : "error");
      setEmbedError(
        launchUrl
          ? null
          : "Set VITE_SUPERSET_DASHBOARD_ID to a valid Superset dashboard id or slug to render analytics inline.",
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
          response.error || "Unable to load the embedded Superset dashboard.",
        );
      }
      return response.data;
    };

    const mountDashboard = async () => {
      setEmbedState("loading");
      setEmbedError(null);

      try {
        const initialPayload = await fetchEmbedPayload();
        if (cancelled || !mountRef.current) {
          return;
        }

        const embeddedDashboardId = initialPayload.embedded_uuid?.trim();
        if (!embeddedDashboardId) {
          throw new Error(
            "Superset did not return an embedded dashboard identifier.",
          );
        }

        firstGuestToken = initialPayload.guest_token;
        setEmbedDomain(initialPayload.superset_domain.replace(/\/$/, ""));

        embeddedDashboard = await embedDashboard({
          id: embeddedDashboardId,
          supersetDomain: initialPayload.superset_domain,
          mountPoint: mountRef.current,
          fetchGuestToken: async () => {
            if (firstGuestToken) {
              const token = firstGuestToken;
              firstGuestToken = null;
              return token;
            }
            const refreshedPayload = await fetchEmbedPayload();
            setEmbedDomain(refreshedPayload.superset_domain.replace(/\/$/, ""));
            return refreshedPayload.guest_token;
          },
          dashboardUiConfig: {
            hideTitle: false,
            hideTab: false,
            hideChartControls: false,
            filters: {
              visible: true,
              expanded: false,
            },
          },
          iframeTitle: "Embedded Superset dashboard",
          iframeSandboxExtras: [
            "allow-top-navigation-by-user-activation",
            "allow-popups-to-escape-sandbox",
          ],
        });

        if (!cancelled) {
          setEmbedState("ready");
        }
      } catch (error) {
        if (cancelled || !mountRef.current) {
          return;
        }
        mountRef.current.replaceChildren();
        setEmbedError(
          error instanceof Error
            ? error.message
            : "Unable to load the embedded Superset dashboard.",
        );
        setEmbedState(launchUrl ? "fallback" : "error");
      }
    };

    mountDashboard();

    return () => {
      cancelled = true;
      if (embeddedDashboard) {
        embeddedDashboard.unmount();
      }
      if (mountRef.current) {
        mountRef.current.replaceChildren();
      }
    };
  }, [dashboardRef, launchUrl, refreshKey]);

  const StatusIcon = statusMeta.icon;

  return (
    <TooltipProvider delayDuration={200}>
      <motion.div
        className="space-y-5"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      >
        {/* Header */}
        <div className="space-y-3 px-1">
          <div className="flex items-center gap-2">
            <span className="section-kicker">Chart Workspace</span>
            <Badge
              variant={statusMeta.variant}
              className={`gap-1.5 text-xs font-medium ${statusMeta.bg} ${statusMeta.color} ${statusMeta.border}`}
            >
              <StatusIcon
                className={`h-3 w-3 ${statusMeta.pulse ? "animate-spin" : ""}`}
              />
              {statusMeta.label}
              {statusMeta.pulse && (
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-500" />
                </span>
              )}
            </Badge>
          </div>

          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="section-title">Embedded Chart Builder</h2>
              <p className="section-subtitle max-w-3xl">
                Use the embedded Superset dashboard for review, then launch full Superset when you need SQL Lab or chart authoring.
              </p>
            </div>

            {/* Toolbar */}
            <div className="flex flex-wrap items-center gap-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleRefresh}
                    disabled={embedState === "loading"}
                  >
                    <RefreshCw
                      className={`h-4 w-4 mr-1.5 ${embedState === "loading" ? "animate-spin" : ""}`}
                    />
                    Refresh
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Reload embedded dashboard</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={toggleFullscreen}
                  >
                    {isFullscreen ? (
                      <Minimize2 className="h-4 w-4 mr-1.5" />
                    ) : (
                      <Maximize2 className="h-4 w-4 mr-1.5" />
                    )}
                    {isFullscreen ? "Exit" : "Fullscreen"}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  {isFullscreen ? "Exit fullscreen" : "Expand to fullscreen"}
                </TooltipContent>
              </Tooltip>

              <Separator orientation="vertical" className="h-6 hidden sm:block" />

              {launchUrl ? (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="outline" size="sm" asChild>
                      <a href={launchUrl} target="_blank" rel="noreferrer">
                        <ExternalLink className="mr-1.5 h-4 w-4" />
                        Open Superset
                      </a>
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Open full Superset in new tab</TooltipContent>
                </Tooltip>
              ) : null}
            </div>
          </div>
        </div>

        {/* Main Card */}
        <Card
          ref={cardRef}
          className="superset-workspace-card gap-0 w-full overflow-hidden"
          style={{
            minHeight: isFullscreen
              ? "100vh"
              : "clamp(32rem, calc(100vh - 11rem), 54rem)",
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
                      <BarChart3 className="h-4 w-4" />
                      <span>Embedded analytics canvas</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {embedState === "ready" && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 border border-emerald-200"
                        >
                          <span className="relative flex h-1.5 w-1.5">
                            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
                          </span>
                          Live
                        </motion.div>
                      )}
                    </div>
                  </div>

                  {/* Canvas */}
                  <div className="flex min-h-0 flex-1 bg-background/70 p-3">
                    <div
                      className="superset-embedded-frame relative w-full overflow-hidden rounded-2xl border border-border/70 bg-white shadow-sm dark:bg-slate-950"
                      style={{
                        minHeight: isFullscreen
                          ? "calc(100vh - 3.5rem)"
                          : "clamp(28rem, calc(100vh - 16rem), 50rem)",
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
                            {/* Skeleton layout */}
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
                                  Loading embedded analytics…
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
                <motion.div
                  key="error"
                  className="flex min-h-[28rem] flex-col items-center justify-center gap-5 px-6 text-center"
                  initial={{ opacity: 0, scale: 0.97 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.97 }}
                  transition={{ duration: 0.3 }}
                >
                  <motion.div
                    initial={{ y: 10, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.1 }}
                    className="rounded-full border border-border/70 bg-background/80 p-4"
                  >
                    {launchUrl ? (
                      <AlertTriangle className="h-8 w-8 text-amber-500" />
                    ) : (
                      <Settings className="h-8 w-8 text-slate-400" />
                    )}
                  </motion.div>

                  <div className="space-y-2">
                    <Badge
                      variant="outline"
                      className="text-xs font-semibold uppercase tracking-[0.18em]"
                    >
                      {launchUrl ? "Launch required" : "Not configured"}
                    </Badge>
                    <h3 className="text-2xl font-semibold tracking-tight text-foreground">
                      {launchUrl
                        ? "Embedded analytics unavailable"
                        : "Superset dashboard not configured"}
                    </h3>
                    <p className="max-w-xl text-sm leading-7 text-muted-foreground">
                      {embedError
                        ? embedError
                        : launchUrl
                          ? "Open the full Superset workspace in a new tab while the embedded dashboard is unavailable."
                          : `Configure the embedded analytics URL with VITE_SUPERSET_URL or store it in local storage under ${SUPERSET_URL_KEY}.`}
                    </p>
                  </div>

                  <div className="flex flex-wrap items-center justify-center gap-3">
                    {launchUrl ? (
                      <Button asChild>
                        <a href={launchUrl} target="_blank" rel="noreferrer">
                          <ExternalLink className="mr-2 h-4 w-4" />
                          Open Superset Workspace
                        </a>
                      </Button>
                    ) : null}
                    <Button variant="outline" onClick={handleRefresh}>
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Retry
                    </Button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </CardContent>
        </Card>
      </motion.div>
    </TooltipProvider>
  );
}
