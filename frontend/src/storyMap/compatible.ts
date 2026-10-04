import type { RiverThread } from "../api/types";

/** Two readings could be the same story: one schema, and wherever both cast a role, the same entity
 * (and at least one role cast by both). Threads of different audiences are matched this way, because
 * their core readings need not be equally specific. */
export function compatible(first: RiverThread, second: RiverThread): boolean {
  if (first.schema_slug !== second.schema_slug) {
    return false;
  }
  const cast = new Map(first.binding.map((entry) => [entry.role, entry.entity_id]));
  const shared = second.binding.filter((entry) => entry.entity_id !== null && cast.get(entry.role) != null);
  return shared.length > 0 && shared.every((entry) => cast.get(entry.role) === entry.entity_id);
}
