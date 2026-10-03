import { useSearchParams } from "react-router";

import type { ChronicleDetail } from "../api/types";
import { ALL_BEATS } from "./AudienceSelect";

/** The audience and point in time a chronicle screen shows, kept in the address (?audience=&t=). */
export function useChronicleView(chronicle: ChronicleDetail) {
  const [searchParams, setSearchParams] = useSearchParams();
  const audience = searchParams.get("audience") ?? ALL_BEATS;
  const chosenT = searchParams.get("t");

  const query = new URLSearchParams({ audience });
  if (chosenT !== null) {
    query.set("t", chosenT);
  }

  function choose(changes: Record<string, string>) {
    setSearchParams({ ...Object.fromEntries(searchParams), ...changes });
  }

  return {
    audience,
    chosenT,
    t: chosenT === null ? chronicle.last_t : Number(chosenT),
    query: query.toString(),
    selectedHypothesis: searchParams.get("hypothesis"),
    chooseAudience: (value: string) => choose({ audience: value }),
    chooseT: (value: number) => choose({ t: String(value) }),
    chooseHypothesis: (id: number) => choose({ hypothesis: String(id) }),
  };
}
