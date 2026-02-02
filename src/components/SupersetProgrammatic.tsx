import { useEffect, useState } from "react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Input } from "./ui/input";
import { Label } from "./ui/label";

const defaultDomain = import.meta.env.VITE_SUPERSET_URL || "http://localhost:8088";

const defaultDashboardId = Number(import.meta.env.VITE_SUPERSET_DASHBOARD_ID || 0);
const SUPERSET_URL_STORAGE_KEY = "biolink.superset.url";

export function SupersetProgrammatic() {
  const [url, setUrl] = useState("");
  const [activeUrl, setActiveUrl] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = window.localStorage.getItem(SUPERSET_URL_STORAGE_KEY);
    const defaultUrl = defaultDashboardId
      ? `${defaultDomain}/superset/dashboard/${defaultDashboardId}/`
      : defaultDomain;

    if (stored) {
      setUrl(stored);
      setActiveUrl(stored);
      return;
    }

    setUrl(defaultUrl);
    setActiveUrl(defaultUrl);
  }, []);

  const handleLoadUrl = () => {
    const nextUrl = url.trim();
    if (!nextUrl) return;
    setActiveUrl(nextUrl);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(SUPERSET_URL_STORAGE_KEY, nextUrl);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Superset Live (Programmatic)</CardTitle>
          <p className="text-sm text-muted-foreground">
            Load the Superset UI directly inside the app. Use this to build dashboards and panels in Superset itself.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-4 items-end">
            <div className="space-y-2">
              <Label>Superset URL</Label>
              <Input value={url} onChange={e => setUrl(e.target.value)} />
            </div>
            <Button onClick={handleLoadUrl}>Load Superset</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Embedded Superset</CardTitle>
          <p className="text-sm text-muted-foreground">
            Superset UI appears below once loaded.
          </p>
        </CardHeader>
        <CardContent>
          {activeUrl ? (
            <iframe title="Superset" src={activeUrl} className="w-full min-h-[800px] rounded-md border" />
          ) : (
            <div className="min-h-[600px] w-full rounded-md border bg-background flex items-center justify-center text-sm text-muted-foreground">
              Enter a Superset URL to load the UI.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
