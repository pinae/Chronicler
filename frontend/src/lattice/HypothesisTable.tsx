import type { LatticeHypothesis } from "../api/types";

type Props = {
  schemaName: string;
  hypotheses: LatticeHypothesis[];
};

/** The hypotheses of one schema, strongest first. */
export function HypothesisTable({ schemaName, hypotheses }: Props) {
  const strongestFirst = [...hypotheses].sort((first, second) => second.weight - first.weight);
  return (
    <table aria-label={schemaName}>
      <thead>
        <tr>
          <th scope="col">Binding</th>
          <th scope="col">Status</th>
          <th scope="col">Weight</th>
          <th scope="col">Filled steps</th>
          <th scope="col">Open steps</th>
        </tr>
      </thead>
      <tbody>
        {strongestFirst.map((hypothesis) => (
          <tr key={hypothesis.id}>
            <td>
              {bindingText(hypothesis)}
              {hypothesis.voiced && " (voiced)"}
            </td>
            <td>{hypothesis.status}</td>
            <td>{hypothesis.weight.toFixed(2)}</td>
            <td>{filledStepsText(hypothesis)}</td>
            <td>{hypothesis.open_steps.join(", ")}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function bindingText(hypothesis: LatticeHypothesis): string {
  return hypothesis.binding.map((entry) => `${entry.role} = ${entry.entity_name ?? "?"}`).join(", ");
}

function filledStepsText(hypothesis: LatticeHypothesis): string {
  return hypothesis.filled_steps.map((step) => `${step.step_id} (t=${step.beat_ts.join(", ")})`).join("; ");
}
