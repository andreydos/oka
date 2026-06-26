import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { HealthStatus } from "../types";

export function HealthIndicator() {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    const check = async () => {
      try {
        setHealth(await api.health());
      } catch {
        setHealth(null);
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  if (!health) {
    return (
      <span className="inline-flex items-center gap-2 text-sm text-red-600">
        <span className="h-2 w-2 rounded-full bg-red-500" />
        Offline
      </span>
    );
  }

  const ok = health.status === "ok";
  return (
    <span
      className={`inline-flex items-center gap-2 text-sm ${ok ? "text-green-700" : "text-amber-700"}`}
      title={`DB: ${health.database}, Qdrant: ${health.qdrant}, Ollama: ${health.ollama}${health.ollama_busy ? " (busy)" : ""}`}
    >
      <span className={`h-2 w-2 rounded-full ${ok ? "bg-green-500" : "bg-amber-500"}`} />
      {health.ollama_busy ? "Ollama busy" : ok ? "Ready" : "Degraded"}
    </span>
  );
}
