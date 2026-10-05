import type { KnowledgeCell, KnowledgeColumn } from "../api/types";

/** A beat learned after it happened: it burns from its own row (t) down to the row it was learned. */
export type Fuse = { t: number; knownSinceT: number; lane: number };

/** Every beat the player learned later. A fuse's first stretch runs across its own row to its lane,
 * so every fuse that starts while it burns (or where it ends) takes a lane inside it: no fuse
 * crosses another. */
export function fuses(column: KnowledgeColumn): Fuse[] {
  const latestFirst = column.known.filter(learnedLater).sort((first, second) => second.t - first.t);
  const placed: Fuse[] = [];
  for (const cell of latestFirst) {
    const inside = placed.filter((fuse) => fuse.t > cell.t && fuse.t <= cell.known_since_t);
    const lane = Math.max(-1, ...inside.map((fuse) => fuse.lane)) + 1;
    placed.push({ t: cell.t, knownSinceT: cell.known_since_t, lane });
  }
  return placed.reverse();
}

export function learnedLater(cell: KnowledgeCell): boolean {
  return cell.known_since_t > cell.t;
}

/** How a player came to know a beat (undefined: they never did). */
export function howKnown(cell: KnowledgeCell | undefined): string {
  if (cell === undefined) {
    return "not learned";
  }
  if (!learnedLater(cell)) {
    return "when it happened";
  }
  if (cell.learned_via_t === null) {
    return `shown at t = ${cell.known_since_t}`;
  }
  return `learned at t = ${cell.known_since_t} via beat ${cell.learned_via_t}`;
}
