import { Link, useParams } from "react-router";

import type { ChronicleDetail, EntitySummary, KnownBeat } from "../api/types";
import { useApi } from "../api/useApi";
import { TimeSlider } from "../chronicle/TimeSlider";
import { useChronicleView } from "../chronicle/useChronicleView";
import { KnowerSelect } from "./KnowerSelect";
import { KnowledgeTable } from "./KnowledgeTable";

export function KnowledgePage() {
  const { chronicleId } = useParams();
  const chronicle = useApi<ChronicleDetail>(`/api/chronicles/${chronicleId}`);
  const characters = useApi<EntitySummary[]>(`/api/chronicles/${chronicleId}/entities?kind=character`);

  if (chronicle.status === "loading" || characters.status === "loading") {
    return <p>Loading…</p>;
  }
  if (chronicle.status === "error" || characters.status === "error") {
    return <p role="alert">Could not load the chronicle.</p>;
  }
  return <KnowledgeView chronicle={chronicle.data} characters={characters.data} />;
}

function KnowledgeView({
  chronicle,
  characters,
}: {
  chronicle: ChronicleDetail;
  characters: EntitySummary[];
}) {
  const view = useChronicleView(chronicle);
  const knower = view.param("knower") ?? "";

  return (
    <main>
      <p>
        <Link to={`/chronicles/${chronicle.id}`}>Beats of {chronicle.title}</Link>
      </p>
      <h1>Who knows what in {chronicle.title}</h1>
      <KnowerSelect
        characters={characters}
        players={chronicle.players}
        value={knower}
        onChange={(value) => view.choose({ knower: value })}
      />
      <TimeSlider t={view.t} lastT={chronicle.last_t} onChange={view.chooseT} />
      {knower === "" ? (
        <p>Choose a character or a player.</p>
      ) : (
        <KnownBeats chronicleId={chronicle.id} knower={knower} chosenT={view.chosenT} />
      )}
    </main>
  );
}

type KnownBeatsProps = {
  chronicleId: number;
  knower: string;
  chosenT: string | null;
};

function KnownBeats({ chronicleId, knower, chosenT }: KnownBeatsProps) {
  const [kind = "", id = ""] = knower.split("-");
  const query = new URLSearchParams({ [kind]: id });
  if (chosenT !== null) {
    query.set("t", chosenT);
  }
  const beats = useApi<KnownBeat[]>(`/api/chronicles/${chronicleId}/knowledge?${query}`);

  if (beats.status === "loading") {
    return <p>Loading…</p>;
  }
  if (beats.status === "error") {
    return <p role="alert">Could not load what they know.</p>;
  }
  return <KnowledgeTable beats={beats.data} knowerIsPlayer={kind === "player"} />;
}
