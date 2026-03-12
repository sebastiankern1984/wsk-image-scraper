import { ImageOff } from "lucide-react";

export interface ProductSummary {
  product_id: string;
  name: string;
  ean: string | null;
  pzn: string | null;
  image_count: number;
  pending_count: number;
  accepted_count: number;
  rejected_count: number;
  thumbnail_url: string | null;
}

interface ProductImageCardProps {
  product: ProductSummary;
  onClick: () => void;
}

export default function ProductImageCard({
  product,
  onClick,
}: ProductImageCardProps) {
  const borderColor =
    product.accepted_count > 0
      ? "border-emerald-500/50"
      : product.pending_count > 0
        ? "border-amber-500/50"
        : "border-border";

  return (
    <button
      onClick={onClick}
      className={`rounded-lg border-2 ${borderColor} bg-card text-left overflow-hidden transition-colors hover:bg-accent/50 focus:outline-none focus:ring-2 focus:ring-ring w-full`}
    >
      {/* Thumbnail */}
      <div className="aspect-square bg-muted flex items-center justify-center overflow-hidden">
        {product.thumbnail_url ? (
          <img
            src={product.thumbnail_url}
            alt={product.name}
            className="w-full h-full object-contain"
            loading="lazy"
          />
        ) : (
          <ImageOff className="h-10 w-10 text-muted-foreground" />
        )}
      </div>

      {/* Info */}
      <div className="p-3 space-y-1">
        <p className="text-sm font-medium leading-tight line-clamp-2">
          {product.name}
        </p>
        <div className="flex gap-2 text-xs text-muted-foreground">
          {product.ean && <span>EAN: {product.ean}</span>}
          {product.pzn && <span>PZN: {product.pzn}</span>}
        </div>
        <div className="flex items-center gap-1.5 pt-1">
          <span
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
              product.image_count > 0
                ? "bg-primary/20 text-primary"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {product.image_count} Bilder
          </span>
        </div>
      </div>
    </button>
  );
}
