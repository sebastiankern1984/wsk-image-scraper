import { useEffect, useState, useCallback } from "react";
import {
  X,
  Check,
  XCircle,
  Loader2,
  ExternalLink,
  CheckCircle,
  ImageOff,
} from "lucide-react";
import { apiFetch } from "@/lib/api";

interface ImageData {
  image_id: string;
  source: string;
  status: string;
  thumbnail_url: string;
  file_url: string;
}

interface ImageCurationModalProps {
  productId: string;
  productName: string;
  open: boolean;
  onClose: () => void;
  onUpdate: () => void;
}

const sourceBadgeColors: Record<string, string> = {
  openfoodfacts: "bg-green-500/20 text-green-400 border-green-500/30",
  google: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  bing: "bg-orange-500/20 text-orange-400 border-orange-500/30",
};

const statusBadgeColors: Record<string, string> = {
  pending: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  accepted: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  rejected: "bg-red-500/20 text-red-400 border-red-500/30",
};

export default function ImageCurationModal({
  productId,
  productName,
  open,
  onClose,
  onUpdate,
}: ImageCurationModalProps) {
  const [images, setImages] = useState<ImageData[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [bulkLoading, setBulkLoading] = useState(false);

  const fetchImages = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch<ImageData[]>(
        `/api/products/${productId}/images`,
      );
      setImages(data);
    } catch {
      // silently handle
    } finally {
      setLoading(false);
    }
  }, [productId]);

  useEffect(() => {
    if (open) {
      fetchImages();
    }
  }, [open, fetchImages]);

  // Close on Escape key
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (open) {
      document.addEventListener("keydown", handleKey);
      return () => document.removeEventListener("keydown", handleKey);
    }
  }, [open, onClose]);

  async function acceptImage(imageId: string) {
    setActionLoading(imageId);
    try {
      await apiFetch(`/api/images/${imageId}/accept`, { method: "PUT" });
      await fetchImages();
      onUpdate();
    } catch {
      // silently handle
    } finally {
      setActionLoading(null);
    }
  }

  async function rejectImage(imageId: string) {
    setActionLoading(imageId);
    try {
      await apiFetch(`/api/images/${imageId}/reject`, { method: "PUT" });
      await fetchImages();
      onUpdate();
    } catch {
      // silently handle
    } finally {
      setActionLoading(null);
    }
  }

  async function acceptAll() {
    setBulkLoading(true);
    try {
      const pending = images.filter((img) => img.status === "pending");
      for (const img of pending) {
        await apiFetch(`/api/images/${img.image_id}/accept`, { method: "PUT" });
      }
      await fetchImages();
      onUpdate();
    } catch {
      // silently handle
    } finally {
      setBulkLoading(false);
    }
  }

  if (!open) return null;

  const hasPending = images.some((img) => img.status === "pending");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-3xl max-h-[85vh] rounded-lg border border-border bg-card shadow-xl mx-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-5 py-4 shrink-0">
          <h2 className="text-lg font-semibold line-clamp-1 pr-4">
            {productName}
          </h2>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Bulk actions */}
        {hasPending && !loading && (
          <div className="border-b border-border px-5 py-3 shrink-0">
            <button
              onClick={acceptAll}
              disabled={bulkLoading}
              className="inline-flex items-center gap-2 rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 transition-colors disabled:opacity-50"
            >
              {bulkLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <CheckCircle className="h-4 w-4" />
              )}
              Alle akzeptieren
            </button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="flex items-center justify-center h-40">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : images.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 gap-2 text-muted-foreground">
              <ImageOff className="h-10 w-10" />
              <p>Keine Bilder gefunden</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {images.map((img) => {
                const isCurated = img.status !== "pending";
                const isLoading = actionLoading === img.image_id;

                return (
                  <div
                    key={img.image_id}
                    className="rounded-lg border border-border bg-background overflow-hidden"
                  >
                    {/* Thumbnail */}
                    <a
                      href={img.file_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block aspect-square bg-muted relative group"
                    >
                      <img
                        src={img.thumbnail_url}
                        alt=""
                        className="w-full h-full object-contain"
                        loading="lazy"
                      />
                      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                        <ExternalLink className="h-5 w-5 text-white" />
                      </div>
                    </a>

                    {/* Badges + actions */}
                    <div className="p-2 space-y-2">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span
                          className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium ${sourceBadgeColors[img.source] ?? "bg-muted text-muted-foreground border-border"}`}
                        >
                          {img.source}
                        </span>
                        <span
                          className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium ${statusBadgeColors[img.status] ?? statusBadgeColors.pending}`}
                        >
                          {img.status}
                        </span>
                      </div>

                      <div className="flex gap-2">
                        <button
                          onClick={() => acceptImage(img.image_id)}
                          disabled={isLoading || (isCurated && img.status === "accepted")}
                          className="flex-1 inline-flex items-center justify-center gap-1 rounded-md bg-emerald-600/20 px-2 py-1 text-xs font-medium text-emerald-400 hover:bg-emerald-600/30 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                          {isLoading ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <Check className="h-3 w-3" />
                          )}
                          Akzeptieren
                        </button>
                        <button
                          onClick={() => rejectImage(img.image_id)}
                          disabled={isLoading || (isCurated && img.status === "rejected")}
                          className="flex-1 inline-flex items-center justify-center gap-1 rounded-md bg-red-600/20 px-2 py-1 text-xs font-medium text-red-400 hover:bg-red-600/30 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                          {isLoading ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <XCircle className="h-3 w-3" />
                          )}
                          Ablehnen
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
