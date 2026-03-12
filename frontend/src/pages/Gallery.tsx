import { useEffect, useState, useCallback } from "react";
import {
  Loader2,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import ProductImageCard, {
  type ProductSummary,
} from "@/components/ProductImageCard";
import ImageCurationModal from "@/components/ImageCurationModal";

interface ProductsResponse {
  products: ProductSummary[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

const FILTERS = [
  { key: "all", label: "Alle" },
  { key: "uncurated", label: "Unkuratiert" },
  { key: "accepted", label: "Akzeptiert" },
  { key: "rejected", label: "Abgelehnt" },
  { key: "no_images", label: "Keine Bilder" },
] as const;

type FilterKey = (typeof FILTERS)[number]["key"];

export default function Gallery() {
  const [filter, setFilter] = useState<FilterKey>("all");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<ProductsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal state
  const [selectedProduct, setSelectedProduct] = useState<ProductSummary | null>(
    null,
  );

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch<ProductsResponse>(
        `/api/products?page=${page}&per_page=50&filter=${filter}`,
      );
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  }, [page, filter]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  function changeFilter(key: FilterKey) {
    setFilter(key);
    setPage(1);
  }

  const totalPages = data?.total_pages ?? 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <h1 className="text-2xl font-bold">Galerie</h1>

      {/* Filter tabs */}
      <div className="flex flex-wrap gap-1 border-b border-border pb-1">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => changeFilter(f.key)}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              filter === f.key
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center h-64 gap-4">
          <AlertTriangle className="h-10 w-10 text-destructive" />
          <p className="text-destructive">{error}</p>
          <button
            onClick={fetchProducts}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Erneut versuchen
          </button>
        </div>
      ) : data && data.products.length === 0 ? (
        <div className="flex items-center justify-center h-64 text-muted-foreground">
          Keine Produkte gefunden.
        </div>
      ) : data ? (
        <>
          {/* Product grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {data.products.map((product) => (
              <ProductImageCard
                key={product.product_id}
                product={product}
                onClick={() => setSelectedProduct(product)}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 pt-4">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="inline-flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-accent transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" />
                Zurück
              </button>
              <span className="text-sm text-muted-foreground">
                Seite {page} von {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="inline-flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-accent transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              >
                Weiter
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </>
      ) : null}

      {/* Curation Modal */}
      {selectedProduct && (
        <ImageCurationModal
          productId={selectedProduct.product_id}
          productName={selectedProduct.name}
          open={!!selectedProduct}
          onClose={() => setSelectedProduct(null)}
          onUpdate={fetchProducts}
        />
      )}
    </div>
  );
}
