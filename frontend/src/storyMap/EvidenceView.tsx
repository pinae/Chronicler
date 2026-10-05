import { useId, useState } from "react";

import type { BeatSummary, River } from "../api/types";
import { EvidenceMatrix } from "./EvidenceMatrix";
import styles from "./EvidenceView.module.css";

/** The evidence matrix of one audience, up to a chosen beat. */
export function EvidenceView({ beats, river }: { beats: BeatSummary[]; river: River }) {
  const [audience, setAudience] = useState(river.columns[0]?.audience ?? "all");
  const [upTo, setUpTo] = useState(String(river.last_t));
  const audienceId = useId();
  const upToId = useId();
  const column = river.columns.find((candidate) => candidate.audience === audience) ?? river.columns[0];
  if (!column) {
    return null;
  }
  return (
    <section>
      <div className={styles.controls}>
        <span>
          <label htmlFor={audienceId}>Seen by</label>{" "}
          <select
            id={audienceId}
            value={column.audience}
            onChange={(event) => setAudience(event.target.value)}
          >
            {river.columns.map((candidate) => (
              <option key={candidate.audience} value={candidate.audience}>
                {candidate.name}
              </option>
            ))}
          </select>
        </span>
        <span>
          <label htmlFor={upToId}>Up to beat</label>{" "}
          <input
            id={upToId}
            type="number"
            min={1}
            max={river.last_t}
            value={upTo}
            onChange={(event) => setUpTo(event.target.value)}
          />
        </span>
      </div>
      <EvidenceMatrix beats={beats} column={column} upToT={chosenBeat(upTo, river.last_t)} />
    </section>
  );
}

/** The beat typed in, kept within the chronicle; the last beat while the field is empty. */
function chosenBeat(typed: string, lastT: number): number {
  const t = Number.parseInt(typed, 10);
  return Number.isNaN(t) ? lastT : Math.min(lastT, Math.max(1, t));
}
