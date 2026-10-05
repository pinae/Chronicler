import type { BeatSummary, KnowledgeMap } from "../api/types";
import { howKnown } from "./knowledgeLayout";

/** The knowledge map's facts as a table: the accessible twin of the chart. */
export function WhoKnewWhatTable({
  beats,
  knowledgeMap,
}: {
  beats: BeatSummary[];
  knowledgeMap: KnowledgeMap;
}) {
  const players = knowledgeMap.columns.map((column) => ({
    id: column.player,
    name: column.name,
    known: new Map(column.known.map((cell) => [cell.t, cell])),
  }));
  return (
    <table aria-label="Who knew what">
      <thead>
        <tr>
          <th scope="col">t</th>
          <th scope="col">Beat</th>
          {players.map((player) => (
            <th key={player.id} scope="col">
              {player.name}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {beats.map((beat) => (
          <tr key={beat.t}>
            <td>{beat.t}</td>
            <td>{beat.text}</td>
            {players.map((player) => (
              <td key={player.id}>{howKnown(player.known.get(beat.t))}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
