import { useState } from "react";

import type { BeatSummary, River } from "../api/types";
import { BeatRows, ROW_HEIGHT } from "./BeatRows";
import { MapColumn } from "./MapColumn";
import { MapToolbar } from "./MapToolbar";
import { PacingChart } from "./PacingChart";
import { PacingLegend } from "./PacingLegend";
import { PacingTable } from "./PacingTable";

const COLUMN_WIDTH = 96;

/** How each beat moved each audience: surprise and tension, one column per audience. */
export function PacingView({ beats, river }: { beats: BeatSummary[]; river: River }) {
  const [asTable, setAsTable] = useState(false);
  return (
    <section>
      <MapToolbar
        legend={<PacingLegend />}
        asTable={asTable}
        onToggle={() => setAsTable(!asTable)}
        chartName="chart"
      />
      {asTable ? (
        <PacingTable river={river} />
      ) : (
        <BeatRows beats={beats}>
          {river.columns.map((column) => (
            <MapColumn key={column.audience} name={column.name}>
              <PacingChart column={column} width={COLUMN_WIDTH} rowHeight={ROW_HEIGHT} lastT={river.last_t} />
            </MapColumn>
          ))}
        </BeatRows>
      )}
    </section>
  );
}
