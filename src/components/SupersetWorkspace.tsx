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
            <Label>Superset URL</Label>
            <div className="flex gap-2">
              <Input
                placeholder="https://superset.example.com/superset/dashboard/"
                value={url}
                onChange={event => setUrl(event.target.value)}
              />
              <Button onClick={saveUrl}>Save</Button>
              {url && (
                <Button variant="outline" asChild>
                  <a href={url} target="_blank" rel="noreferrer">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Open
                  </a>
                </Button>
              )}
            </div>
          </div>
          <div className="text-xs text-muted-foreground">
            Tip: use Superset embedded dashboard or Explore URL to build and explore dashboards.
          </div>
        </CardContent>
      </Card>

      {url ? (
        <Card>
          <CardContent className="p-0">
            <iframe title="Superset" src={url} className="w-full h-[800px] rounded-md border" />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="text-sm text-muted-foreground py-10 text-center">
            Add a Superset URL to begin.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
