import { useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Image as ImageIcon,
  CheckCircle,
  AlertTriangle,
  Loader2,
  ArrowLeft,
  Square,
} from "lucide-react";
import { apiFetch } from "@/lib/api";

interface BatchDetail {
  batch_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  total_products: number;
  processed: number;
  images_found: number;
  error_count: number;
}

const statusColors: Record<string, string> = {
  running: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  completed: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  failed: "bg-red-500/20 text-red-400 border-red-500/30",
  cancelled: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
};

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusColors[status] ?? statusColors.cancelled}`}
    >
      {status}
    </span>
  );
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function BatchMonitor() {
  const { id } = useParams<{ id: string }>();
  const [batch, setBatch] = useState<BatchDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  async function fetchBatch() {
    try {
      const data = await apiFetch<BatchDetail>(`/api/batches/${id}`);
      setBatch(data);
      if (data.status !== "running" && intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchBatch();
    intervalRef.current = setInterval(fetchBatch, 2000);
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function cancelBatch() {
    if (!confirm("Batch wirklich abbrechen?")) return;
    setCancelling(true);
    try {
      await apiFetch(`/api/batches/${id}/cancel`, { method: "POST" });
      await fetchBatch();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Abbruch fehlgeschlagen");
    } finally {
      setCancelling(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error && !batch) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <AlertTriangle className="h-10 w-10 text-destructive" />
        <p className="text-destructive">{error}</p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Zurück zum Dashboard
        </Link>
      </div>
    );
  }

  if (!batch) return null;

  const pct =
    batch.total_products > 0
      ? Math.round((batch.processed / batch.total_products) * 100)
      : 0;
  const isDone = batch.status !== "running";

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">Batch #{id}</h1>
          <StatusBadge status={batch.status} />
        </div>
        {!isDone && (
          <button
            onClick={cancelBatch}
            disabled={cancelling}
            className="inline-flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-4 py-2 text-sm font-medium text-destructive hover:bg-destructive/20 transition-colors disabled:opacity-50"
          >
            {cancelling ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Square className="h-4 w-4" />
            )}
            Abbrechen
          </button>
        )}
      </div>

      {/* Progress bar */}
      <div className="rounded-lg border border-border bg-card p-5 space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span>
            {batch.processed} / {batch.total_products} Produkte
          </span>
          <span className="font-semibold">{pct}%</span>
        </div>
        <div className="h-3 rounded-full bg-muted overflow-hidden">
          <div
            className="h-full rounded-full bg-primary transition-all duration-500 ease-out"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-lg border border-border bg-card p-4 flex items-center gap-3">
          <ImageIcon className="h-5 w-5 text-muted-foreground" />
          <div>
            <p className="text-xs text-muted-foreground">Bilder gefunden</p>
            <p className="text-xl font-bold">{batch.images_found}</p>
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card p-4 flex items-center gap-3">
          <CheckCircle className="h-5 w-5 text-emerald-400" />
          <div>
            <p className="text-xs text-muted-foreground">Verarbeitet</p>
            <p className="text-xl font-bold">{batch.processed}</p>
          </div>
        </div>
        <div className="rounded-lg border border-border bg-card p-4 flex items-center gap-3">
          <AlertTriangle
            className={`h-5 w-5 ${batch.error_count > 0 ? "text-red-400" : "text-muted-foreground"}`}
          />
          <div>
            <p className="text-xs text-muted-foreground">Fehler</p>
            <p
              className={`text-xl font-bold ${batch.error_count > 0 ? "text-red-400" : ""}`}
            >
              {batch.error_count}
            </p>
          </div>
        </div>
      </div>

      {/* Timestamps */}
      <div className="rounded-lg border border-border bg-card p-5 space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Gestartet:</span>
          <span>{formatDate(batch.started_at)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Beendet:</span>
          <span>
            {batch.completed_at ? formatDate(batch.completed_at) : "Läuft..."}
          </span>
        </div>
      </div>

      {/* Back link */}
      {isDone && (
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Zurück zum Dashboard
        </Link>
      )}
    </div>
  );
}
