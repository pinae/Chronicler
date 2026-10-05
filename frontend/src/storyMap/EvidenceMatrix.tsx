import type { CSSProperties } from "react";

import type { BeatSummary, RiverColumn } from "../api/types";
import styles from "./EvidenceMatrix.module.css";
import { evidenceKind, markOf, readingsAt, type Mark } from "./evidence";
import { schemaColor } from "./schemaColors";
import { percent, threadLabel } from "./threadLabel";

type Props = { beats: BeatSummary[]; column: RiverColumn; upToT: number };

/** Heuer's matrix of competing hypotheses: the beats up to `upToT` against the readings of one
 * audience, each cell the steps a beat filled for a reading or its refutation. */
export function EvidenceMatrix({ beats, column, upToT }: Props) {
  const readings = readingsAt(column, upToT);
  return (
    <div className={styles.scroll}>
      <table aria-label={`Evidence seen by ${column.name}`}>
        <thead>
          <tr>
            <th scope="col">t</th>
            <th scope="col">Beat</th>
            {readings.map(({ thread, share }) => (
              <th
                key={thread.id}
                scope="col"
                className={styles.reading}
                style={{ "--reading-color": schemaColor(thread.schema_slug) } as CSSProperties}
              >
                {`${threadLabel(thread)} (${share === null ? "refuted" : percent(share)})`}
              </th>
            ))}
            <th scope="col">Evidence</th>
          </tr>
        </thead>
        <tbody>
          {beats
            .filter((beat) => beat.t <= upToT)
            .map((beat) => {
              const marks = readings.map(({ thread }) => markOf(column, thread, beat.t));
              const kind = evidenceKind(marks);
              return (
                <tr key={beat.t} className={styles.row} data-evidence={kind}>
                  <td>{beat.t}</td>
                  <td className={styles.beat}>{beat.text}</td>
                  {readings.map(({ thread }, index) => (
                    <MarkCell key={thread.id} mark={marks[index] ?? null} />
                  ))}
                  <td>{kind}</td>
                </tr>
              );
            })}
        </tbody>
      </table>
    </div>
  );
}

/** The steps a beat filled, then its refutation, set apart. */
function MarkCell({ mark }: { mark: Mark | null }) {
  if (mark === null) {
    return <td />;
  }
  return (
    <td>
      {mark.steps.join(", ")}
      {mark.refuted && (
        <>
          {mark.steps.length > 0 && ", "}
          <span className={styles.refuted}>refuted</span>
        </>
      )}
    </td>
  );
}
