import { useEffect, useMemo, useRef, useState } from "react";
import { embedDashboard } from "@superset-ui/embedded-sdk";
import { ExternalLink, Loader2 } from "lucide-react";
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { getSupersetDashboardEmbed } from "../api/superset";

const SUPERSET_URL_KEY = "biolink.superset.url";
const CONFIGURED_DASHBOARD_ID = Number(
  String(import.meta.env.VITE_SUPERSET_DASHBOARD_ID ?? "").trim(),
);

function getConfiguredDashboardId() {
  return Number.isInteger(CONFIGURED_DASHBOARD_ID) && CONFIGURED_DASHBOARD_ID > 0
    ? CONFIGURED_DASHBOARD_ID
    : null;
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
  const mountRef = useRef<HTMLDivElement | null>(null);
  const dashboardId = getConfiguredDashboardId();

  const launchUrl = useMemo(() => {
    const baseUrl = (embedDomain || url).replace(/\/$/, "");
    if (!baseUrl) {
      return "";
    }
    if (dashboardId) {
      return `${baseUrl}/superset/dashboard/${dashboardId}/`;
    }
    return `${baseUrl}/superset/welcome/`;
  }, [dashboardId, embedDomain, url]);

  const statusLabel =
    embedState === "ready"
      ? "Embedded dashboard live"
      : embedState === "loading"
        ? "Connecting to Superset"
        : launchUrl
          ? "Superset launch ready"
          : "Superset connection required";

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
    if (!dashboardId) {
      setEmbedState(launchUrl ? "fallback" : "error");
      setEmbedError(
        launchUrl
          ? null
          : "Set VITE_SUPERSET_DASHBOARD_ID to a valid embeddable dashboard ID to render analytics inline.",
      );
      mountRef.current.replaceChildren();
      return;
    }

    let cancelled = false;
    let embeddedDashboard: { unmount: () => void } | null = null;
    let firstGuestToken: string | null = null;

    const fetchEmbedPayload = async () => {
      const response = await getSupersetDashboardEmbed({
        dashboard_id: dashboardId,
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

        firstGuestToken = initialPayload.guest_token;
        setEmbedDomain(initialPayload.superset_domain.replace(/\/$/, ""));

        embeddedDashboard = await embedDashboard({
          id: String(dashboardId),
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
  }, [dashboardId, launchUrl]);

  return (
    <div className="space-y-5">
      <div className="space-y-2 px-1">
        <span className="section-kicker">Chart Workspace</span>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="section-title">Embedded Chart Builder</h2>
            <p className="section-subtitle max-w-3xl">
              Use the embedded Superset dashboard for review, then launch full Superset when you need SQL Lab or chart authoring.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {launchUrl ? (
              <Button variant="outline" asChild>
                <a href={launchUrl} target="_blank" rel="noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Open Full Superset
                </a>
              </Button>
            ) : null}
            <div className="rounded-full border border-border/70 bg-background/80 px-4 py-2 text-sm text-muted-foreground">
              {statusLabel}
            </div>
          </div>
        </div>
      </div>

      <Card
        className="superset-workspace-card gap-0 w-full overflow-hidden"
        style={{ minHeight: "clamp(32rem, calc(100vh - 11rem), 54rem)" }}
      >
        <CardContent className="flex min-h-0 w-full flex-1 flex-col p-0">
          {embedState === "ready" || embedState === "loading" ? (
            <>
              <div className="border-b border-border/70 bg-muted/20 px-5 py-3 text-sm text-muted-foreground">
                Embedded analytics canvas. Use the dashboard below for review and launch the full Superset workspace in a new tab for deeper editing.
              </div>
              <div className="flex min-h-0 flex-1 bg-background/70 p-3">
                <div
                  className="superset-embedded-frame relative w-full overflow-hidden rounded-2xl border border-border/70 bg-white shadow-sm"
                  style={{ minHeight: "clamp(28rem, calc(100vh - 16rem), 50rem)" }}
                >
                  <div ref={mountRef} className="superset-embedded-mount h-full w-full" />
                  {embedState === "loading" ? (
                    <div className="absolute inset-0 flex items-center justify-center bg-white/88 backdrop-blur-sm">
                      <div className="flex items-center gap-3 rounded-full border border-border/70 bg-background px-4 py-2 text-sm text-muted-foreground shadow-sm">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Loading embedded analytics...
                      </div>
                    </div>
                  ) : null}
                </div>
              </div>
            </>
          ) : (
            <div className="flex min-h-[28rem] flex-col items-center justify-center gap-4 px-6 text-center">
              <div className="rounded-full border border-border/70 bg-background/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                {launchUrl ? "Launch required" : "Not configured"}
              </div>
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
              {launchUrl ? (
                <Button asChild>
                  <a href={launchUrl} target="_blank" rel="noreferrer">
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Open Superset Workspace
                  </a>
                </Button>
              ) : null}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
