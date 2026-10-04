import { useState } from "react";

import type { BeatSummary, River, RiverThread } from "../api/types";
import { Legend } from "./Legend";
import { RiverChart } from "./RiverChart";
import { RiverTables } from "./RiverTables";
import styles from "./StoryMap.module.css";

export const ROW_HEIGHT = 32;
const COLUMN_WIDTH = 140;

/** The beats down the left, one river per audience beside them, every beat one row. */
export function StoryMap({ beats, river }: { beats: BeatSummary[]; river: River }) {
  const [asTable, setAsTable] = useState(false);
  const [highlighted, setHighlighted] = useState<RiverThread | null>(null);

  return (
    <section>
      <div className={styles.toolbar}>
        <Legend river={river} />
        <button type="button" onClick={() => setAsTable(!asTable)}>
          {asTable ? "Show as river" : "Show as table"}
        </button>
      </div>
      {asTable ? (
        <RiverTables river={river} />
      ) : (
        <div className={styles.map} style={{ "--row-height": `${ROW_HEIGHT}px` } as React.CSSProperties}>
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
          {river.columns.map((column) => (
            <div key={column.audience} className={styles.column}>
              <div className={styles.columnName}>{column.name}</div>
              <RiverChart
                column={column}
                width={COLUMN_WIDTH}
                rowHeight={ROW_HEIGHT}
                highlighted={highlighted}
                onHighlight={setHighlighted}
              />
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
