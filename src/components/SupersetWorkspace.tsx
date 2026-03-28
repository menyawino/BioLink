import { useEffect, useState } from "react";
import { Card, CardContent } from "./ui/card";

const SUPERSET_URL_KEY = "biolink.superset.url";
const DEFAULT_SUPERSET_URL = import.meta.env.VITE_SUPERSET_URL?.trim() ?? "";

export function SupersetWorkspace() {
  const [url, setUrl] = useState(DEFAULT_SUPERSET_URL);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = localStorage.getItem(SUPERSET_URL_KEY);
    if (stored?.trim()) {
      setUrl(stored);
    } else if (DEFAULT_SUPERSET_URL) {
      localStorage.setItem(SUPERSET_URL_KEY, DEFAULT_SUPERSET_URL);
    }
  }, []);

  return (
    <div className="space-y-5">
      <div className="space-y-2 px-1">
        <span className="section-kicker">Chart Workspace</span>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="section-title">Embedded Chart Builder</h2>
            <p className="section-subtitle max-w-3xl">
              Use the embedded Superset workspace for exploratory charting without leaving the registry shell.
            </p>
          </div>
          <div className="rounded-full border border-border/70 bg-background/80 px-4 py-2 text-sm text-muted-foreground">
            {url ? 'Superset connection configured' : 'Superset connection required'}
          </div>
        </div>
      </div>

      <Card className="superset-workspace-card w-full overflow-hidden">
        <CardContent className="flex min-h-[calc(100vh-12rem)] flex-col p-0">
          {url ? (
            <>
              <div className="border-b border-border/70 bg-muted/20 px-5 py-3 text-sm text-muted-foreground">
                Embedded analytics canvas. Open dashboards, saved charts, or SQL Lab in the panel below.
              </div>
              <div className="min-h-0 flex-1 bg-background/70 p-3">
                <div className="h-full overflow-hidden rounded-2xl border border-border/70 bg-white shadow-sm">
                  <iframe
                    title="Superset"
                    src={url}
                    className="h-full w-full rounded-none border-0"
                  />
                </div>
              </div>
            </>
          ) : (
            <div className="flex min-h-[28rem] flex-col items-center justify-center gap-3 px-6 text-center">
              <div className="rounded-full border border-border/70 bg-background/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Not configured
              </div>
              <h3 className="text-2xl font-semibold tracking-tight text-foreground">Superset URL not set</h3>
              <p className="max-w-xl text-sm leading-7 text-muted-foreground">
                Configure the embedded analytics URL with the <code>VITE_SUPERSET_URL</code> environment variable or store it in local storage under <code>{SUPERSET_URL_KEY}</code>.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
