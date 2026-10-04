import { useParams } from "react-router";

import type { BeatSummary, ChronicleDetail, River } from "../api/types";
import { useApi } from "../api/useApi";
import { ChronicleFrame } from "../shell/ChronicleFrame";
import { StoryMap } from "./StoryMap";

export function StoryMapPage() {
  const { chronicleId } = useParams();
  const chronicle = useApi<ChronicleDetail>(`/api/chronicles/${chronicleId}`);

  if (chronicle.status === "loading") {
    return <p>Loading…</p>;
  }
  if (chronicle.status === "error") {
    return <p role="alert">{chronicle.notFound ? "Chronicle not found" : "Could not load the chronicle."}</p>;
  }
  return <StoryMapView chronicle={chronicle.data} />;
}

function StoryMapView({ chronicle }: { chronicle: ChronicleDetail }) {
  const beats = useApi<BeatSummary[]>(`/api/chronicles/${chronicle.id}/beats?audience=all`);
  const river = useApi<River>(`/api/chronicles/${chronicle.id}/river`);

  return (
    <ChronicleFrame chronicle={chronicle} current="map">
      <h1>Story map of {chronicle.title}</h1>
      <p>
        Every story the engine reads in the chronicle, beat by beat: the wider a band, the more of the
        engine&apos;s belief that reading holds at that beat. One column for all beats (the game master&apos;s
        view), one for each player.
      </p>
      {(beats.status === "loading" || river.status === "loading") && <p>Loading…</p>}
      {(beats.status === "error" || river.status === "error") && (
        <p role="alert">Could not load the story map.</p>
      )}
      {beats.status === "ready" && river.status === "ready" && (
        <StoryMap beats={beats.data} river={river.data} />
      )}
    </ChronicleFrame>
  );
}
