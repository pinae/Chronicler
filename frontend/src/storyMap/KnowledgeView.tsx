import { useState } from "react";

import type { BeatSummary, KnowledgeMap } from "../api/types";
import { BeatRows, ROW_HEIGHT } from "./BeatRows";
import { KnowledgeChart } from "./KnowledgeChart";
import { KnowledgeLegend } from "./KnowledgeLegend";
import { MapColumn } from "./MapColumn";
import { MapToolbar } from "./MapToolbar";
import { WhoKnewWhatTable } from "./WhoKnewWhatTable";

const COLUMN_WIDTH = 72;

/** Who knew which beat from when: one column per player beside the beats. */
export function KnowledgeView({ beats, knowledgeMap }: { beats: BeatSummary[]; knowledgeMap: KnowledgeMap }) {
  const [asTable, setAsTable] = useState(false);
  if (knowledgeMap.columns.length === 0) {
    return <p>Nobody plays at this table, so there is no knowledge to map.</p>;
  }
  return (
    <section>
      <MapToolbar
        legend={<KnowledgeLegend />}
        asTable={asTable}
        onToggle={() => setAsTable(!asTable)}
        chartName="map"
      />
      {asTable ? (
        <WhoKnewWhatTable beats={beats} knowledgeMap={knowledgeMap} />
      ) : (
        <BeatRows beats={beats}>
          {knowledgeMap.columns.map((column) => (
            <MapColumn key={column.player} name={column.name}>
              <KnowledgeChart
                column={column}
                width={COLUMN_WIDTH}
                rowHeight={ROW_HEIGHT}
                lastT={knowledgeMap.last_t}
              />
            </MapColumn>
          ))}
        </BeatRows>
      )}
    </section>
  );
}
