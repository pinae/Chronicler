import type { RiverColumn, RiverThread } from "../api/types";

/** A column of the evidence matrix: a reading's thread with its share at the chosen beat, or null
 * when it was refuted by then. */
export type Reading = { thread: RiverThread; share: number | null };

/** What one beat did to one reading. */
export type Mark = { steps: string[]; refuted: boolean };

/** The readings held at t, strongest first, then those refuted by t (Heuer: keep the rejected
 * hypotheses in view). */
export function readingsAt(column: RiverColumn, t: number): Reading[] {
  const shares = column.moments.find((moment) => moment.t === t)?.shares ?? [];
  const held = [...shares]
    .sort((first, second) => second.share - first.share)
    .flatMap((share) => {
      const thread = column.threads.find((candidate) => candidate.id === share.thread);
      return thread ? [{ thread, share: share.share }] : [];
    });
  const heldIds = new Set(held.map((reading) => reading.thread.id));
  const refuted = column.threads
    .filter((thread) => !heldIds.has(thread.id) && refutedBy(column, thread, t))
    .map((thread) => ({ thread, share: null }));
  return [...held, ...refuted];
}

function refutedBy(column: RiverColumn, thread: RiverThread, t: number): boolean {
  return column.events.some(
    (event) => event.thread === thread.id && event.kind === "refuted" && event.t <= t,
  );
}

/** The steps the beat at t filled for the thread and whether it refuted it; null if it did neither. */
export function markOf(column: RiverColumn, thread: RiverThread, t: number): Mark | null {
  const events = column.events.filter((event) => event.thread === thread.id && event.t === t);
  const steps = events.flatMap((event) => (event.kind === "filled" && event.step ? [event.step] : []));
  const refuted = events.some((event) => event.kind === "refuted");
  return steps.length > 0 || refuted ? { steps, refuted } : null;
}

/** What a beat's row says about the readings: evidence that fits every reading tells nothing apart. */
export function evidenceKind(marks: (Mark | null)[]): string {
  const marked = marks.filter((mark) => mark !== null);
  if (marked.length === 0) {
    return "supports none";
  }
  if (marks.length === 1) {
    return marked[0]?.refuted ? "refutes it" : "supports it";
  }
  if (marked.length < marks.length) {
    return "tells them apart";
  }
  if (marked.every((mark) => !mark.refuted)) {
    return "fits every reading";
  }
  return marked.every((mark) => mark.refuted) ? "refutes every reading" : "tells them apart";
}
