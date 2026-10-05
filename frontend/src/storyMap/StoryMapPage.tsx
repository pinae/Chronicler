import { useParams } from "react-router";

import type { BeatSummary, ChronicleDetail, KnowledgeMap, River } from "../api/types";
import { useApi } from "../api/useApi";
import { ChronicleFrame } from "../shell/ChronicleFrame";
import { KnowledgeView } from "./KnowledgeView";
import { PacingView } from "./PacingView";
import { RiverView } from "./RiverView";
import { StoryMapViews, type StoryMapViewName } from "./StoryMapViews";

export function StoryMapPage({ view = "river" }: { view?: StoryMapViewName }) {
  const { chronicleId } = useParams();
  const chronicle = useApi<ChronicleDetail>(`/api/chronicles/${chronicleId}`);

  if (chronicle.status === "loading") {
    return <p>Loading…</p>;
  }
  if (chronicle.status === "error") {
    return <p role="alert">{chronicle.notFound ? "Chronicle not found" : "Could not load the chronicle."}</p>;
  }
  return <StoryMapScreen chronicle={chronicle.data} view={view} />;
}

function StoryMapScreen({ chronicle, view }: { chronicle: ChronicleDetail; view: StoryMapViewName }) {
  const beats = useApi<BeatSummary[]>(`/api/chronicles/${chronicle.id}/beats?audience=all`);

  return (
    <ChronicleFrame chronicle={chronicle} current="map">
      <h1>Story map of {chronicle.title}</h1>
      <StoryMapViews chronicleId={chronicle.id} current={view} />
      {beats.status === "loading" && <p>Loading…</p>}
      {beats.status === "error" && <p role="alert">Could not load the story map.</p>}
      {beats.status === "ready" && view === "river" && (
        <RiverSection chronicleId={chronicle.id} beats={beats.data} />
      )}
      {beats.status === "ready" && view === "knowledge" && (
        <KnowledgeSection chronicleId={chronicle.id} beats={beats.data} />
      )}
      {beats.status === "ready" && view === "pacing" && (
        <PacingSection chronicleId={chronicle.id} beats={beats.data} />
      )}
    </ChronicleFrame>
  );
}

function RiverSection({ chronicleId, beats }: { chronicleId: number; beats: BeatSummary[] }) {
  const river = useApi<River>(`/api/chronicles/${chronicleId}/river`);
  return (
    <>
      <p>
        Every story the engine reads in the chronicle, beat by beat: the wider a band, the more of the
        engine&apos;s belief that reading holds at that beat. One column for all beats (the game master&apos;s
        view), one for each player.
      </p>
      {river.status === "loading" && <p>Loading…</p>}
      {river.status === "error" && <p role="alert">Could not load the story river.</p>}
      {river.status === "ready" && <RiverView beats={beats} river={river.data} />}
    </>
  );
}

function KnowledgeSection({ chronicleId, beats }: { chronicleId: number; beats: BeatSummary[] }) {
  const knowledgeMap = useApi<KnowledgeMap>(`/api/chronicles/${chronicleId}/knowledge_map`);
  return (
    <>
      <p>
        Who knew which beat from when. A long fuse is a reveal of the past; an empty cell is something a
        player does not know, a secret of the game master or the table&apos;s dramatic irony.
      </p>
      {knowledgeMap.status === "loading" && <p>Loading…</p>}
      {knowledgeMap.status === "error" && <p role="alert">Could not load the knowledge map.</p>}
      {knowledgeMap.status === "ready" && <KnowledgeView beats={beats} knowledgeMap={knowledgeMap.data} />}
    </>
  );
}

function PacingSection({ chronicleId, beats }: { chronicleId: number; beats: BeatSummary[] }) {
  const river = useApi<River>(`/api/chronicles/${chronicleId}/river`);
  return (
    <>
      <p>
        How each beat moved each audience. Surprise is how much of the engine&apos;s belief moved at that
        beat; tension is how much of it rests on stories that are building up, with a development step filled
        and the payoff still open. Both are read from the readings&apos; shares, as in the story river.
      </p>
      {river.status === "loading" && <p>Loading…</p>}
      {river.status === "error" && <p role="alert">Could not load the pacing.</p>}
      {river.status === "ready" && <PacingView beats={beats} river={river.data} />}
    </>
  );
}
