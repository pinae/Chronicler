import { Link, useParams } from "react-router";

import type { ChronicleDetail, EntitySummary, Predicate } from "../api/types";
import { useApi } from "../api/useApi";
import { CandidateBeatForm } from "./CandidateBeatForm";
import { EffectsTable } from "./EffectsTable";
import { useDryRun, type DryRunState } from "./useDryRun";

export function TryBeatPage() {
  const { chronicleId } = useParams();
  const chronicle = useApi<ChronicleDetail>(`/api/chronicles/${chronicleId}`);
  const entities = useApi<EntitySummary[]>(`/api/chronicles/${chronicleId}/entities`);
  const vocabulary = useApi<Predicate[]>("/api/vocabulary");

  if (chronicle.status === "loading" || entities.status === "loading" || vocabulary.status === "loading") {
    return <p>Loading…</p>;
  }
  if (chronicle.status === "error" || entities.status === "error" || vocabulary.status === "error") {
    return <p role="alert">Could not load the chronicle.</p>;
  }
  return <TryBeatView chronicle={chronicle.data} entities={entities.data} vocabulary={vocabulary.data} />;
}

type ViewProps = {
  chronicle: ChronicleDetail;
  entities: EntitySummary[];
  vocabulary: Predicate[];
};

function TryBeatView({ chronicle, entities, vocabulary }: ViewProps) {
  const dryRun = useDryRun(chronicle.id);

  return (
    <main>
      <p>
        <Link to={`/chronicles/${chronicle.id}`}>Beats of {chronicle.title}</Link>
      </p>
      <h1>Try a beat in {chronicle.title}</h1>
      <p>See what a beat would do to the hypotheses before you narrate it. Nothing you try here is kept.</p>
      <CandidateBeatForm
        vocabulary={vocabulary}
        entities={entities}
        players={chronicle.players}
        running={dryRun.state.status === "running"}
        onTry={dryRun.tryBeat}
      />
      <DryRunResult state={dryRun.state} />
    </main>
  );
}

function DryRunResult({ state }: { state: DryRunState }) {
  switch (state.status) {
    case "idle":
      return null;
    case "running":
      return <p>Trying…</p>;
    case "error":
      return <p role="alert">{state.message}</p>;
    case "ready":
      return (
        <section>
          <h2>If this were beat {state.data.t}</h2>
          <EffectsTable effects={state.data.effects} />
        </section>
      );
  }
}
