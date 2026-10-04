import type { River, RiverColumn } from "../api/types";
import { percent, threadLabel } from "./threadLabel";

/** The river's numbers as tables, one per audience: the accessible twin of the chart. */
export function RiverTables({ river }: { river: River }) {
  return (
    <>
      {river.columns.map((column) => (
        <ColumnTable key={column.audience} column={column} />
      ))}
    </>
  );
}

function ColumnTable({ column }: { column: RiverColumn }) {
  const hasOther = column.moments.some((moment) => moment.other > 0);
  return (
    <table aria-label={`Shares seen by ${column.name}`}>
      <caption>{column.name}</caption>
      <thead>
        <tr>
          <th scope="col">t</th>
          {column.threads.map((thread) => (
            <th key={thread.id} scope="col">
              {threadLabel(thread)}
            </th>
          ))}
          {hasOther && <th scope="col">Other readings</th>}
        </tr>
      </thead>
      <tbody>
        {column.moments
          .filter((moment) => moment.t > 0)
          .map((moment) => (
            <tr key={moment.t}>
              <td>{moment.t}</td>
              {column.threads.map((thread) => {
                const share = moment.shares.find((candidate) => candidate.thread === thread.id);
                return (
                  <td key={thread.id}>
                    {share && `${percent(share.share)}${share.secret ? " (secret)" : ""}`}
                  </td>
                );
              })}
              {hasOther && <td>{moment.other > 0 && percent(moment.other)}</td>}
            </tr>
          ))}
      </tbody>
    </table>
  );
}
