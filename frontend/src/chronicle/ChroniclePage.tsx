import { Link, useParams, useSearchParams } from "react-router";

import type { BeatSummary, ChronicleDetail } from "../api/types";
import { useApi } from "../api/useApi";
import { ALL_BEATS, AudienceSelect } from "./AudienceSelect";
import { BeatTable } from "./BeatTable";
import { TimeSlider } from "./TimeSlider";

export function ChroniclePage() {
  const { chronicleId } = useParams();
  const chronicle = useApi<ChronicleDetail>(`/api/chronicles/${chronicleId}`);

  if (chronicle.status === "loading") {
    return <p>Loading…</p>;
  }
  if (chronicle.status === "error") {
    return <p role="alert">{chronicle.notFound ? "Chronicle not found" : "Could not load the chronicle."}</p>;
  }
  return <ChronicleView chronicle={chronicle.data} />;
}

function ChronicleView({ chronicle }: { chronicle: ChronicleDetail }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const audience = searchParams.get("audience") ?? ALL_BEATS;
  const chosenT = searchParams.get("t");
  const t = chosenT === null ? chronicle.last_t : Number(chosenT);

  const query = new URLSearchParams({ audience });
  if (chosenT !== null) {
    query.set("t", chosenT);
  }
  const beats = useApi<BeatSummary[]>(`/api/chronicles/${chronicle.id}/beats?${query}`);

  function choose(changes: Record<string, string>) {
    setSearchParams({ ...Object.fromEntries(searchParams), ...changes });
  }

  return (
    <main>
      <p>
        <Link to="/">All chronicles</Link>
      </p>
      <h1>{chronicle.title}</h1>
      <p>{chronicle.kind}</p>
      <AudienceSelect
        players={chronicle.players}
        value={audience}
        onChange={(value) => choose({ audience: value })}
      />
      <TimeSlider t={t} lastT={chronicle.last_t} onChange={(value) => choose({ t: String(value) })} />
      {beats.status === "loading" && <p>Loading…</p>}
      {beats.status === "error" && <p role="alert">Could not load the beats.</p>}
      {beats.status === "ready" && <BeatTable beats={beats.data} />}
    </main>
  );
}
