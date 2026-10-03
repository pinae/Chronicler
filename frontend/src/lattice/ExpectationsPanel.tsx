import { useId } from "react";

import type { Expectation, LatticeHypothesis } from "../api/types";
import { useApi } from "../api/useApi";
import { bindingText } from "./bindingText";

type Props = {
  chronicleId: number;
  hypothesis: LatticeHypothesis;
  chosenT: string | null;
};

/** What the audience expected next for one hypothesis, as the reader model answered at the chosen beat. */
export function ExpectationsPanel({ chronicleId, hypothesis, chosenT }: Props) {
  const headingId = useId();
  const query = chosenT === null ? "" : `?${new URLSearchParams({ t: chosenT })}`;
  const expectations = useApi<Expectation[]>(
    `/api/chronicles/${chronicleId}/hypotheses/${hypothesis.id}/expectations${query}`,
  );

  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId}>Expectations for {bindingText(hypothesis)}</h2>
      {expectations.status === "loading" && <p>Loading…</p>}
      {expectations.status === "error" && <p role="alert">Could not load the expectations.</p>}
      {expectations.status === "ready" && <ExpectationList expectations={expectations.data} />}
    </section>
  );
}

function ExpectationList({ expectations }: { expectations: Expectation[] }) {
  if (expectations.length === 0) {
    return <p>No expectations yet</p>;
  }
  return expectations.map((expectation, index) => (
    <article key={`${expectation.step_id}-${index}`}>
      <h3>{expectation.question}</h3>
      <p>asked at t = {expectation.computed_at_t}</p>
      <ul>
        {expectation.candidates.map((candidate) => (
          <li key={candidate.label}>
            {candidate.text}: {Math.round(candidate.p * 100)}%
          </li>
        ))}
      </ul>
    </article>
  ));
}
