import { describe, expect, it } from "vitest";

import { compatible } from "./compatible";

function thread(schema: string, ...ids: (number | null)[]) {
  return {
    id: 0,
    schema_slug: schema,
    schema_name: schema,
    binding: ids.map((id, index) => ({ role: "CVI"[index] ?? "X", entity_id: id, entity_name: null })),
    open_steps: [],
    waiting_since: null,
    payoff_steps: ["discovery"],
  };
}

describe("compatible", () => {
  it("holds for readings of one schema that agree wherever both bind a role", () => {
    expect(compatible(thread("hidden_crime", 1, 2, null), thread("hidden_crime", 1, null, 3))).toBe(true);
  });

  it("fails when a role both bind is bound to different entities", () => {
    expect(compatible(thread("hidden_crime", 1, 2, null), thread("hidden_crime", 4, 2, null))).toBe(false);
  });

  it("fails across schemas and when no role is bound by both", () => {
    expect(compatible(thread("hidden_crime", 1, null), thread("betrayal", 1, null))).toBe(false);
    expect(compatible(thread("hidden_crime", 1, null), thread("hidden_crime", null, 2))).toBe(false);
  });
});
