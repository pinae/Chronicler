import { useId, useState } from "react";

import type { BeatSummary, KnowledgeMap, River, RiverColumn } from "../api/types";
import { ClueLedger } from "./ClueLedger";
import { threadLabel } from "./threadLabel";

type Props = { beats: BeatSummary[]; river: River; knowledgeMap: KnowledgeMap };

/** The clue ledger of one of the game master's readings, the strongest at the last beat unless
 * another is chosen. */
export function ClueView({ beats, river, knowledgeMap }: Props) {
  const gameMaster = river.columns.find((column) => column.audience === "all") ?? river.columns[0];
  const [chosen, setChosen] = useState<number | null>(null);
  const pickerId = useId();
  if (!gameMaster) {
    return null;
  }
  const thread =
    gameMaster.threads.find((candidate) => candidate.id === chosen) ?? strongestAtTheEnd(gameMaster);
  if (!thread) {
    return <p>The engine holds no reading of this chronicle yet.</p>;
  }
  return (
    <section>
      <p>
        <label htmlFor={pickerId}>Reading</label>{" "}
        <select id={pickerId} value={thread.id} onChange={(event) => setChosen(Number(event.target.value))}>
          {gameMaster.threads.map((candidate) => (
            <option key={candidate.id} value={candidate.id}>
              {threadLabel(candidate)}
            </option>
          ))}
        </select>
      </p>
      <ClueLedger beats={beats} column={gameMaster} thread={thread} knowledgeMap={knowledgeMap} />
      {thread.open_steps.length > 0 && <p>Still open: {thread.open_steps.join(", ")}</p>}
    </section>
  );
}

function strongestAtTheEnd(column: RiverColumn) {
  const last = column.moments.at(-1);
  const strongest = [...(last?.shares ?? [])].sort((first, second) => second.share - first.share)[0];
  return column.threads.find((thread) => thread.id === strongest?.thread) ?? column.threads[0];
}
