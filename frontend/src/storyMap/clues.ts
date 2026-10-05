import type { KnowledgeCell, RiverColumn, RiverThread } from "../api/types";
import { stepsFilledByBeat } from "./threadSteps";

/** A beat that filled steps of the reading; the clues of the Three Clue Rule. */
export type Clue = { t: number; steps: string[]; payoff: boolean };

const ENOUGH_CLUES = 3;

export function cluesTo(column: RiverColumn, thread: RiverThread): Clue[] {
  return stepsFilledByBeat(column, thread).map(([t, steps]) => ({
    t,
    steps,
    payoff: steps.some((step) => thread.payoff_steps.includes(step)),
  }));
}

/** The beat at which the reading first paid off; null while it has not. */
export function payoffAt(clues: Clue[]): number | null {
  return clues.find((clue) => clue.payoff)?.t ?? null;
}

export type Preparation = { text: string; tooFew: boolean };

/** How well a player was prepared for the payoff: whether they saw the first clue happen (and so
 * knew it from the start), otherwise how many of the clues before the payoff they knew by then. */
export function preparation(clues: Clue[], known: Map<number, KnowledgeCell>): Preparation {
  const first = clues[0];
  if (first && known.get(first.t)?.known_since_t === first.t) {
    return { text: "knew it from the start", tooFew: false };
  }
  const payoff = payoffAt(clues) ?? Infinity;
  const before = clues.filter((clue) => clue.t < payoff);
  const seen = before.filter((clue) => (known.get(clue.t)?.known_since_t ?? Infinity) < payoff).length;
  const count = `${seen} of ${before.length}`;
  return seen < ENOUGH_CLUES
    ? { text: `${count}: fewer than three`, tooFew: true }
    : { text: count, tooFew: false };
}
