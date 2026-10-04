import { useState } from "react";

import { ApiError, postJson } from "../api/client";
import type { CandidateBeat, DryRun } from "../api/types";

export type DryRunState =
  | { status: "idle" }
  | { status: "running" }
  | { status: "error"; message: string }
  | { status: "ready"; data: DryRun };

/** Asks the backend what a candidate beat would do to the lattice; nothing is kept. */
export function useDryRun(chronicleId: number) {
  const [state, setState] = useState<DryRunState>({ status: "idle" });

  function tryBeat(candidate: CandidateBeat) {
    setState({ status: "running" });
    postJson<DryRun>(`/api/chronicles/${chronicleId}/dry-run`, candidate).then(
      (data) => setState({ status: "ready", data }),
      (error: unknown) => setState({ status: "error", message: messageOf(error) }),
    );
  }

  return { state, tryBeat };
}

function messageOf(error: unknown): string {
  if (error instanceof ApiError && error.detail !== null) {
    return error.detail;
  }
  return "Could not try the beat.";
}
