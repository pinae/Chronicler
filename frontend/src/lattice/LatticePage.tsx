import { useParams } from "react-router";

import type { ChronicleDetail, Lattice, LatticeHypothesis } from "../api/types";
import { useApi } from "../api/useApi";
import { AudienceSelect } from "../chronicle/AudienceSelect";
import { TimeSlider } from "../chronicle/TimeSlider";
import { useChronicleView } from "../chronicle/useChronicleView";
import { ChronicleFrame } from "../shell/ChronicleFrame";
import { ExpectationsPanel } from "./ExpectationsPanel";
import { HypothesisTable } from "./HypothesisTable";

export function LatticePage() {
  const { chronicleId } = useParams();
  const chronicle = useApi<ChronicleDetail>(`/api/chronicles/${chronicleId}`);

  if (chronicle.status === "loading") {
    return <p>Loading…</p>;
  }
  if (chronicle.status === "error") {
    return <p role="alert">{chronicle.notFound ? "Chronicle not found" : "Could not load the chronicle."}</p>;
  }
  return <LatticeView chronicle={chronicle.data} />;
}

function LatticeView({ chronicle }: { chronicle: ChronicleDetail }) {
  const view = useChronicleView(chronicle);
  const lattice = useApi<Lattice>(`/api/chronicles/${chronicle.id}/lattice?${view.query}`);

  return (
    <ChronicleFrame chronicle={chronicle} current="lattice">
      <h1>Lattice of {chronicle.title}</h1>
      <AudienceSelect
        players={chronicle.players}
        value={view.audience}
        onChange={view.chooseAudience}
        includeTable={false}
      />
      <TimeSlider t={view.t} lastT={chronicle.last_t} onChange={view.chooseT} />
      {lattice.status === "loading" && <p>Loading…</p>}
      {lattice.status === "error" && <p role="alert">Could not load the lattice.</p>}
      {lattice.status === "ready" && (
        <>
          <SchemaSections hypotheses={lattice.data.hypotheses} onShowExpectations={view.chooseHypothesis} />
          <SelectedExpectations
            chronicleId={chronicle.id}
            hypotheses={lattice.data.hypotheses}
            selected={view.selectedHypothesis}
            chosenT={view.chosenT}
          />
        </>
      )}
    </ChronicleFrame>
  );
}

type SchemaSectionsProps = {
  hypotheses: LatticeHypothesis[];
  onShowExpectations: (hypothesisId: number) => void;
};

function SchemaSections({ hypotheses, onShowExpectations }: SchemaSectionsProps) {
  if (hypotheses.length === 0) {
    return <p>No hypotheses at this point</p>;
  }
  const bySchema = Map.groupBy(hypotheses, (hypothesis) => hypothesis.schema_name);
  return [...bySchema].map(([schemaName, schemaHypotheses]) => (
    <section key={schemaName}>
      <h2>{schemaName}</h2>
      <HypothesisTable
        schemaName={schemaName}
        hypotheses={schemaHypotheses}
        onShowExpectations={onShowExpectations}
      />
    </section>
  ));
}

type SelectedExpectationsProps = {
  chronicleId: number;
  hypotheses: LatticeHypothesis[];
  selected: string | null;
  chosenT: string | null;
};

function SelectedExpectations({ chronicleId, hypotheses, selected, chosenT }: SelectedExpectationsProps) {
  const hypothesis = hypotheses.find((candidate) => String(candidate.id) === selected);
  if (!hypothesis) {
    return null;
  }
  return <ExpectationsPanel chronicleId={chronicleId} hypothesis={hypothesis} chosenT={chosenT} />;
}
