import type { RiverColumn, RiverThread } from "../api/types";

/** The beats that filled the thread's steps in this column, in order, with the steps each filled. */
export function stepsFilledByBeat(column: RiverColumn, thread: RiverThread): [number, string[]][] {
  const byT = new Map<number, string[]>();
  for (const event of column.events) {
    if (event.thread === thread.id && event.kind === "filled" && event.step && event.t > 0) {
      byT.set(event.t, [...(byT.get(event.t) ?? []), event.step]);
    }
  }
  return [...byT.entries()].sort(([first], [second]) => first - second);
}
