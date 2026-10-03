import type { LatticeHypothesis } from "../api/types";

/** "T = Aldric, V = Mira, S = ?": who a hypothesis casts in which role. */
export function bindingText(hypothesis: LatticeHypothesis): string {
  return hypothesis.binding.map((entry) => `${entry.role} = ${entry.entity_name ?? "?"}`).join(", ");
}
