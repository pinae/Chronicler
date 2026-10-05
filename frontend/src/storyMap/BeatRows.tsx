import type { CSSProperties, ReactNode } from "react";

import type { BeatSummary } from "../api/types";
import styles from "./BeatRows.module.css";

export const ROW_HEIGHT = 32;

/** The beats down the left and a view's columns beside them, every beat one row. */
export function BeatRows({ beats, children }: { beats: BeatSummary[]; children: ReactNode }) {
  return (
    <div className={styles.map} style={{ "--row-height": `${ROW_HEIGHT}px` } as CSSProperties}>
      <table aria-label="Beats" className={styles.beats}>
        <thead>
          <tr>
            <th scope="col">t</th>
            <th scope="col">Beat</th>
          </tr>
        </thead>
        <tbody>
          {beats.map((beat) => (
            <tr key={beat.t}>
              <td>{beat.t}</td>
              <td title={beat.text}>{beat.text}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {children}
    </div>
  );
}
