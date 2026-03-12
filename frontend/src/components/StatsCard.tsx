interface StatsCardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  variant?: "default" | "success" | "warning" | "danger";
}

const variantStyles: Record<string, string> = {
  default: "text-foreground",
  success: "text-emerald-400",
  warning: "text-amber-400",
  danger: "text-red-400",
};

export default function StatsCard({
  label,
  value,
  icon,
  variant = "default",
}: StatsCardProps) {
  return (
    <div className="rounded-lg border border-border bg-card p-4 flex items-start gap-4">
      <div className={`mt-0.5 ${variantStyles[variant]}`}>{icon}</div>
      <div className="flex flex-col">
        <span className="text-sm text-muted-foreground">{label}</span>
        <span className={`text-2xl font-bold ${variantStyles[variant]}`}>
          {value}
        </span>
      </div>
    </div>
  );
}
