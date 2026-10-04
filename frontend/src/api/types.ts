import type { components } from "./schema";

// Generated from the backend's OpenAPI schema: `yarn generate:api-types`.
export type ChronicleSummary = components["schemas"]["ChronicleSummary"];
export type ChronicleDetail = components["schemas"]["ChronicleDetail"];
export type BeatSummary = components["schemas"]["BeatSummary"];
export type Lattice = components["schemas"]["LatticeOut"];
export type LatticeHypothesis = components["schemas"]["LatticeHypothesisOut"];
export type Expectation = components["schemas"]["ExpectationOut"];
export type KnownBeat = components["schemas"]["KnownBeat"];
export type EntitySummary = components["schemas"]["EntityOut"];
export type Predicate = components["schemas"]["PredicateOut"];
export type Role = components["schemas"]["RoleOut"];
export type DryRun = components["schemas"]["DryRunOut"];
export type Effect = components["schemas"]["EffectOut"];
/** A beat to try before narrating it; the dry run has no use for its text. */
export type CandidateBeat = Omit<components["schemas"]["CandidateBeatIn"], "text">;
