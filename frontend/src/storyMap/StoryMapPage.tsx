import type { ReactNode } from "react";
import { useParams } from "react-router";

import type { BeatSummary, ChronicleDetail, KnowledgeMap, River } from "../api/types";
import { useApi } from "../api/useApi";
import { ChronicleFrame } from "../shell/ChronicleFrame";
import { ClueView } from "./ClueView";
import { EvidenceView } from "./EvidenceView";
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
      {beats.status === "ready" && <ViewSection view={view} chronicleId={chronicle.id} beats={beats.data} />}
    </ChronicleFrame>
  );
}

type SectionProps = { chronicleId: number; beats: BeatSummary[] };

function ViewSection({ view, ...props }: SectionProps & { view: StoryMapViewName }) {
  switch (view) {
    case "river":
      return <RiverSection {...props} />;
    case "knowledge":
      return <KnowledgeSection {...props} />;
    case "pacing":
      return <PacingSection {...props} />;
    case "evidence":
      return <EvidenceSection {...props} />;
    case "clues":
      return <CluesSection {...props} />;
  }
}

const riverOf = (chronicleId: number) => `/api/chronicles/${chronicleId}/river`;
const knowledgeMapOf = (chronicleId: number) => `/api/chronicles/${chronicleId}/knowledge_map`;

function RiverSection({ chronicleId, beats }: SectionProps) {
  return (
    <>
      <p>
        Every story the engine reads in the chronicle, beat by beat: the wider a band, the more of the
        engine&apos;s belief that reading holds at that beat. One column for all beats (the game master&apos;s
        view), one for each player.
      </p>
      <Loaded<River> path={riverOf(chronicleId)} name="story river">
        {(river) => <RiverView beats={beats} river={river} />}
      </Loaded>
    </>
  );
}

function KnowledgeSection({ chronicleId, beats }: SectionProps) {
  return (
    <>
      <p>
        Who knew which beat from when. A long fuse is a reveal of the past; an empty cell is something a
        player does not know, a secret of the game master or the table&apos;s dramatic irony.
      </p>
      <Loaded<KnowledgeMap> path={knowledgeMapOf(chronicleId)} name="knowledge map">
        {(knowledgeMap) => <KnowledgeView beats={beats} knowledgeMap={knowledgeMap} />}
      </Loaded>
    </>
  );
}

function PacingSection({ chronicleId, beats }: SectionProps) {
  return (
    <>
      <p>
        How each beat moved each audience. Surprise is how much of the engine&apos;s belief moved at that
        beat; tension is how much of it rests on stories that are building up, with a development step filled
        and the payoff still open. Both are read from the readings&apos; shares, as in the story river.
      </p>
      <Loaded<River> path={riverOf(chronicleId)} name="pacing">
        {(river) => <PacingView beats={beats} river={river} />}
      </Loaded>
    </>
  );
}

function EvidenceSection({ chronicleId, beats }: SectionProps) {
  return (
    <>
      <p>
        Every beat against the competing readings, as in Heuer&apos;s analysis of competing hypotheses: a cell
        names the steps a beat filled for a reading, or its refutation. A beat that tells the readings apart
        carries the plot; one that fits every reading proves little; one that supports none of them sets the
        scene or misleads.
      </p>
      <Loaded<River> path={riverOf(chronicleId)} name="evidence">
        {(river) => <EvidenceView beats={beats} river={river} />}
      </Loaded>
    </>
  );
}

function CluesSection({ chronicleId, beats }: SectionProps) {
  return (
    <>
      <p>
        The Three Clue Rule: for any conclusion the players should reach, give them at least three clues. Here
        the clues are the beats that filled a reading&apos;s steps, and the ledger shows which of them each
        player knew before the reading paid off.
      </p>
      <Loaded<River> path={riverOf(chronicleId)} name="readings">
        {(river) => (
          <Loaded<KnowledgeMap> path={knowledgeMapOf(chronicleId)} name="knowledge map">
            {(knowledgeMap) => <ClueView beats={beats} river={river} knowledgeMap={knowledgeMap} />}
          </Loaded>
        )}
      </Loaded>
    </>
  );
}

/** Shows its children once the data at `path` has loaded. */
function Loaded<T>({
  path,
  name,
  children,
}: {
  path: string;
  name: string;
  children: (data: T) => ReactNode;
}) {
  const state = useApi<T>(path);
  if (state.status === "loading") {
    return <p>Loading…</p>;
  }
  if (state.status === "error") {
    return <p role="alert">Could not load the {name}.</p>;
  }
  return children(state.data);
}
