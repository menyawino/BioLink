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
    <Card className="w-full h-[calc(100vh-5.5rem)] max-h-[calc(100vh-5.5rem)]">
      <CardContent className="flex-1 min-h-0 p-0">
        {url ? (
          <iframe
            title="Superset"
            src={url}
            className="w-full h-full rounded-none border-0"
          />
        ) : (
          <div className="text-sm text-muted-foreground py-10 text-center">Superset is not configured.</div>
        )}
      </CardContent>
    </Card>
  );
}
