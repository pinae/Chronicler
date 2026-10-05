import { useId, useState } from "react";

import type { River, RiverColumn, RiverThread } from "../api/types";
import styles from "./OpenThreads.module.css";
import { threadLabel } from "./threadLabel";

type Props = {
  river: River;
  onSelect: (column: RiverColumn, thread: RiverThread) => void;
};

/** The game master's list of loaded guns: per audience, the readings with required steps still open,
 * the longest waiting first. */
export function OpenThreads({ river, onSelect }: Props) {
  const [audience, setAudience] = useState(river.columns[0]?.audience ?? "all");
  const pickerId = useId();
  const column = river.columns.find((candidate) => candidate.audience === audience) ?? river.columns[0];
  if (!column) {
    return null;
  }
  const open = column.threads
    .filter((thread) => thread.open_steps.length > 0)
    .sort((first, second) => (first.waiting_since ?? Infinity) - (second.waiting_since ?? Infinity));
  return (
    <section className={styles.panel}>
      <h2>Open threads</h2>
      <label htmlFor={pickerId}>Open threads seen by</label>{" "}
      <select id={pickerId} value={column.audience} onChange={(event) => setAudience(event.target.value)}>
        {river.columns.map((candidate) => (
          <option key={candidate.audience} value={candidate.audience}>
            {candidate.name}
          </option>
        ))}
      </select>
      {open.length === 0 ? (
        <p>Every reading {column.name} holds has filled its required steps.</p>
      ) : (
        <ul aria-label={`Open threads seen by ${column.name}`} className={styles.list}>
          {open.map((thread) => (
            <li key={thread.id}>
              <button type="button" className={styles.thread} onClick={() => onSelect(column, thread)}>
                {threadLabel(thread)}
              </button>
              {` · open: ${thread.open_steps.join(", ")} · `}
              {thread.waiting_since === null
                ? "no beat supports it yet"
                : `waiting since t = ${thread.waiting_since}`}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
