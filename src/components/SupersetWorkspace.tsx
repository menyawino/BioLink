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
