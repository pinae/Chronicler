import type { ChronicleSummary } from "../api/types";
import { useApi } from "../api/useApi";
import { ChronicleList } from "./ChronicleList";

export function ChroniclesPage() {
  const chronicles = useApi<ChronicleSummary[]>("/api/chronicles/");

  return (
    <main>
      <h1>Chronicles</h1>
      {chronicles.status === "loading" && <p>Loading…</p>}
      {chronicles.status === "error" && <p role="alert">Could not load the chronicles.</p>}
      {chronicles.status === "ready" && <ChronicleList chronicles={chronicles.data} />}
    </main>
  );
}
