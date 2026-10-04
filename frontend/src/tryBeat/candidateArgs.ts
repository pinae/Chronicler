import type { Predicate, Role } from "../api/types";

/** How the form fills a role: with an entity, a beat's t or a plain value, in that preference. */
export type FieldKind = "entity" | "beat" | "literal";

const FIELD_KINDS: FieldKind[] = ["entity", "beat", "literal"];

/** Null for roles that only take a proposition, which the form cannot compose. */
export function fieldKindOf(role: Role): FieldKind | null {
  return FIELD_KINDS.find((kind) => role.kinds.includes(kind)) ?? null;
}

/** The beat arguments for the roles given a value: {"who": {"entity": 12}, "what": {"beat": 13}}. */
export function argsOf(predicate: Predicate, roleValues: Record<string, string>): Record<string, unknown> {
  const entries = predicate.roles.flatMap((role) => {
    const value = roleValues[role.name] ?? "";
    const kind = fieldKindOf(role);
    if (value === "" || kind === null) {
      return [];
    }
    return [[role.name, { [kind]: kind === "literal" ? value : Number(value) }]];
  });
  return Object.fromEntries(entries);
}
