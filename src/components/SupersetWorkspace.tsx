import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { ExternalLink, PlugZap } from "lucide-react";

const SUPERSET_URL_KEY = "biolink.superset.url";

export function SupersetWorkspace() {
  const [url, setUrl] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = localStorage.getItem(SUPERSET_URL_KEY);
    if (stored) setUrl(stored);
  }, []);

  const saveUrl = () => {
    localStorage.setItem(SUPERSET_URL_KEY, url);
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PlugZap className="h-5 w-5" />
            Superset Studio
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Embed Apache Superset for 50+ chart types, SQL lab, streaming dashboards, and advanced cross-filtering.
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-1">
            <Label>Superset</Label>
            <div className="flex items-center justify-between gap-2">
              <div className="text-sm text-muted-foreground">
                Embedded Superset (static). The dashboard below will fill the tab.
              </div>
              {url ? (
                <Button variant="outline" asChild>
                  <a href={url} target="_blank" rel="noreferrer">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Open
                  </a>
                </Button>
              ) : (
                <div className="text-xs text-muted-foreground">Superset not configured</div>
              )}
            </div>
          </div>
          <div className="text-xs text-muted-foreground">
            Tip: use Superset embedded dashboard or Explore URL to build and explore dashboards.
          </div>
        </CardContent>
      </Card>

      <Card className="h-full">
        <CardContent className="p-0 h-full">
          {url ? (
            <iframe
              title="Superset"
              src={url}
              className="w-full h-[calc(100vh-6rem)] rounded-none border-0"
            />
          ) : (
            <div className="text-sm text-muted-foreground py-10 text-center">Superset is not configured.</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
