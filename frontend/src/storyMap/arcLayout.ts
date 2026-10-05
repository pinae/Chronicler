import type { RiverColumn, RiverThread } from "../api/types";
import { rowCenter } from "./riverLayout";
import { stepsFilledByBeat } from "./threadSteps";

export type StepPoint = { t: number; y: number; steps: string[] };
export type Arc = { from: StepPoint; to: StepPoint; path: string };

export type ThreadArcs = {
  points: StepPoint[];
  arcs: Arc[];
  /** From the last filled step down to the end: the required steps still open. */
  toCome: { y1: number; y2: number; steps: string[] } | null;
};

/** The beats at which the thread's steps were filled, one arc from each to the next, bulging out
 * from the lane's right edge (`edge`) by more the further apart they are. */
export function threadArcs(
  column: RiverColumn,
  thread: RiverThread,
  rowHeight: number,
  edge: number,
  lastT: number,
): ThreadArcs {
  const points = stepsFilledByBeat(column, thread).map(([t, steps]) => ({
    t,
    y: rowCenter(t, rowHeight),
    steps,
  }));
  const arcs = points.slice(1).map((to, index) => {
    const from = points[index] as StepPoint;
    return { from, to, path: arcPath(from.y, to.y, edge) };
  });
  const last = points.at(-1);
  const toCome =
    thread.open_steps.length > 0
      ? { y1: last?.y ?? 0, y2: lastT * rowHeight, steps: thread.open_steps }
      : null;
  return { points, arcs, toCome };
}

function arcPath(y1: number, y2: number, edge: number): string {
  const bulge = Math.min(edge - 8, Math.max(12, (y2 - y1) / 2));
  return `M${edge} ${y1}C${edge - bulge} ${y1} ${edge - bulge} ${y2} ${edge} ${y2}`;
}
