import { useParams } from "react-router";

import type { BeatSummary, ChronicleDetail } from "../api/types";
import { useApi } from "../api/useApi";
import { ChronicleFrame } from "../shell/ChronicleFrame";
import { AudienceSelect } from "./AudienceSelect";
import { BeatTable } from "./BeatTable";
import { TimeSlider } from "./TimeSlider";
import { useChronicleView } from "./useChronicleView";

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
  const view = useChronicleView(chronicle);
  const beats = useApi<BeatSummary[]>(`/api/chronicles/${chronicle.id}/beats?${view.query}`);

  return (
    <ChronicleFrame chronicle={chronicle} current="beats">
      <h1>{chronicle.title}</h1>
      <p>{chronicle.kind}</p>
      <AudienceSelect players={chronicle.players} value={view.audience} onChange={view.chooseAudience} />
      <TimeSlider t={view.t} lastT={chronicle.last_t} onChange={view.chooseT} />
      {beats.status === "loading" && <p>Loading…</p>}
      {beats.status === "error" && <p role="alert">Could not load the beats.</p>}
      {beats.status === "ready" && <BeatTable beats={beats.data} />}
    </ChronicleFrame>
  );
}
