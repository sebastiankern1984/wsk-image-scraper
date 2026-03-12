import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Package,
  Image as ImageIcon,
  ImageOff,
  Play,
  Loader2,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import StatsCard from "@/components/StatsCard";

interface BatchInfo {
  batch_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  total_products: number;
  processed: number;
  images_found: number;
}

interface ApiUsage {
  used: number;
  limit: number;
}

interface StatsResponse {
  total_products: number;
  products_with_images: number;
  products_without_images: number;
  total_images: number;
  pending_images: number;
  accepted_images: number;
  rejected_images: number;
  last_batch: BatchInfo | null;
  google_usage: ApiUsage;
  bing_usage: ApiUsage;
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
  });
}

function QuotaCard({
  label,
  used,
  limit,
}: {
  label: string;
  used: number;
  limit: number;
}) {
  const pct = limit > 0 ? Math.min((used / limit) * 100, 100) : 0;
  const barColor =
    pct > 90
      ? "bg-red-500"
      : pct > 70
        ? "bg-amber-500"
        : "bg-emerald-500";

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <p className="text-sm text-muted-foreground mb-2">{label}</p>
      <p className="text-lg font-bold mb-2">
        {used.toLocaleString("de-DE")} / {limit.toLocaleString("de-DE")}
      </p>
      <div className="h-2 rounded-full bg-muted overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-xs text-muted-foreground mt-1">
        {pct.toFixed(1)}% verbraucht
      </p>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  async function fetchStats() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<StatsResponse>("/api/stats");
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchStats();
  }, []);

  async function startBatch() {
    setStarting(true);
    try {
      const res = await apiFetch<{ batch_id: string }>("/api/batches/start", {
        method: "POST",
      });
      navigate(`/batches/${res.batch_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Batch konnte nicht gestartet werden");
      setStarting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <AlertTriangle className="h-10 w-10 text-destructive" />
        <p className="text-destructive">{error}</p>
        <button
          onClick={fetchStats}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          Erneut versuchen
        </button>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button
          onClick={startBatch}
          disabled={starting}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {starting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Play className="h-4 w-4" />
          )}
          Batch starten
        </button>
      </div>

      {/* Error banner */}
      {error && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Product stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatsCard
          label="Produkte gesamt"
          value={stats.total_products}
          icon={<Package className="h-5 w-5" />}
        />
        <StatsCard
          label="Mit Bildern"
          value={stats.products_with_images}
          icon={<ImageIcon className="h-5 w-5" />}
          variant="success"
        />
        <StatsCard
          label="Ohne Bilder"
          value={stats.products_without_images}
          icon={<ImageOff className="h-5 w-5" />}
          variant="warning"
        />
      </div>

      {/* Image stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatsCard
          label="Bilder gesamt"
          value={stats.total_images}
          icon={<ImageIcon className="h-4 w-4" />}
        />
        <StatsCard
          label="Unkuratiert"
          value={stats.pending_images}
          icon={<Clock className="h-4 w-4" />}
          variant="warning"
        />
        <StatsCard
          label="Akzeptiert"
          value={stats.accepted_images}
          icon={<CheckCircle className="h-4 w-4" />}
          variant="success"
        />
        <StatsCard
          label="Abgelehnt"
          value={stats.rejected_images}
          icon={<XCircle className="h-4 w-4" />}
          variant="danger"
        />
      </div>

      {/* Last Batch */}
      {stats.last_batch && (
        <div className="rounded-lg border border-border bg-card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Letzter Batch</h2>
            <StatusBadge status={stats.last_batch.status} />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
            <div>
              <span className="text-muted-foreground">Gestartet:</span>{" "}
              {formatDate(stats.last_batch.started_at)}
            </div>
            <div>
              <span className="text-muted-foreground">Fortschritt:</span>{" "}
              {stats.last_batch.processed} / {stats.last_batch.total_products}
            </div>
            <div>
              <span className="text-muted-foreground">Bilder gefunden:</span>{" "}
              {stats.last_batch.images_found}
            </div>
          </div>
        </div>
      )}

      {/* API Quotas */}
      <div>
        <h2 className="text-lg font-semibold mb-3">API-Kontingente</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <QuotaCard
            label="Google Custom Search"
            used={stats.google_usage.used}
            limit={stats.google_usage.limit}
          />
          <QuotaCard
            label="Bing Image Search"
            used={stats.bing_usage.used}
            limit={stats.bing_usage.limit}
          />
        </div>
      </div>
    </div>
  );
}
