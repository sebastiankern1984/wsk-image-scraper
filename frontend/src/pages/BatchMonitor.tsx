import { useParams } from "react-router-dom";

export default function BatchMonitor() {
  const { id } = useParams<{ id: string }>();

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Batch #{id}</h1>
      <p className="text-muted-foreground">
        Detailansicht und Fortschritt des Batches.
      </p>
    </div>
  );
}
