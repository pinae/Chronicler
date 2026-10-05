import { useEffect, useState } from "react";

import type { BeatSummary, River, RiverColumn, RiverThread } from "../api/types";
import { ArcLane } from "./ArcLane";
import { BeatRows, ROW_HEIGHT } from "./BeatRows";
import { Legend } from "./Legend";
import { MapColumn } from "./MapColumn";
import { MapToolbar } from "./MapToolbar";
import { OpenThreads } from "./OpenThreads";
import { RiverChart } from "./RiverChart";
import { RiverTables } from "./RiverTables";

const COLUMN_WIDTH = 140;
const ARC_LANE_WIDTH = 110;

type Selection = { audience: string; threadId: number };

/** The story river beside the beats: one river per audience, the selected thread's arcs, the open
 * threads below. */
export function RiverView({ beats, river }: { beats: BeatSummary[]; river: River }) {
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
      <MapToolbar
        legend={<Legend river={river} />}
        asTable={asTable}
        onToggle={() => setAsTable(!asTable)}
        chartName="river"
      />
      {asTable ? (
        <RiverTables river={river} />
      ) : (
        <BeatRows beats={beats}>
          <ArcLane selected={selected} width={ARC_LANE_WIDTH} rowHeight={ROW_HEIGHT} lastT={river.last_t} />
          {river.columns.map((column) => (
            <MapColumn key={column.audience} name={column.name}>
              <RiverChart
                column={column}
                width={COLUMN_WIDTH}
                rowHeight={ROW_HEIGHT}
                highlighted={pointed ?? selected?.thread ?? null}
                onHighlight={setPointed}
                onSelect={(thread) => select(column, thread)}
              />
            </MapColumn>
          ))}
        </BeatRows>
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
