import { useEffect, useState, type CSSProperties } from "react";

import type { BeatSummary, River, RiverColumn, RiverThread } from "../api/types";
import { ArcLane } from "./ArcLane";
import { Legend } from "./Legend";
import { OpenThreads } from "./OpenThreads";
import { RiverChart } from "./RiverChart";
import { RiverTables } from "./RiverTables";
import styles from "./StoryMap.module.css";

export const ROW_HEIGHT = 32;
const COLUMN_WIDTH = 140;
const ARC_LANE_WIDTH = 110;

type Selection = { audience: string; threadId: number };

/** The beats down the left, one river per audience beside them, every beat one row. */
export function StoryMap({ beats, river }: { beats: BeatSummary[]; river: River }) {
  const [asTable, setAsTable] = useState(false);
  const [pointed, setPointed] = useState<RiverThread | null>(null);
  const [selection, setSelection] = useState<Selection | null>(null);
  const selected = selectedThread(river, selection);

  useEffect(() => {
    if (selection === null) {
      return;
    }
    const clear = (event: KeyboardEvent) => event.key === "Escape" && setSelection(null);
    document.addEventListener("keydown", clear);
    return () => document.removeEventListener("keydown", clear);
  }, [selection]);

  function select(column: RiverColumn, thread: RiverThread | null) {
    const same = selection?.audience === column.audience && selection.threadId === thread?.id;
    setSelection(thread === null || same ? null : { audience: column.audience, threadId: thread.id });
  }

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
          <ArcLane selected={selected} width={ARC_LANE_WIDTH} rowHeight={ROW_HEIGHT} lastT={river.last_t} />
          {river.columns.map((column) => (
            <div key={column.audience} className={styles.column}>
              <div className={styles.columnName}>{column.name}</div>
              <RiverChart
                column={column}
                width={COLUMN_WIDTH}
                rowHeight={ROW_HEIGHT}
                highlighted={pointed ?? selected?.thread ?? null}
                onHighlight={setPointed}
                onSelect={(thread) => select(column, thread)}
              />
            </div>
          ))}
        </div>
      )}
      <OpenThreads river={river} onSelect={select} />
    </section>
  );
}

function selectedThread(river: River, selection: Selection | null) {
  const column = river.columns.find((candidate) => candidate.audience === selection?.audience);
  const thread = column?.threads.find((candidate) => candidate.id === selection?.threadId);
  return column && thread ? { column, thread } : null;
}
