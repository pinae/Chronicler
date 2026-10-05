import type { River } from "../api/types";
import { percent } from "./threadLabel";

/** The pacing's numbers as a table: the accessible twin of the chart. */
export function PacingTable({ river }: { river: River }) {
  const beats = Array.from({ length: river.last_t }, (_, index) => index + 1);
  return (
    <table aria-label="Pacing">
      <thead>
        <tr>
          <th scope="col">t</th>
          {river.columns.map((column) => [
            <th key={`${column.audience}-surprise`} scope="col">{`${column.name}: surprise`}</th>,
            <th key={`${column.audience}-tension`} scope="col">{`${column.name}: tension`}</th>,
          ])}
        </tr>
      </thead>
      <tbody>
        {beats.map((t) => (
          <tr key={t}>
            <td>{t}</td>
            {river.columns.map((column) => {
              const moment = column.moments.find((candidate) => candidate.t === t);
              return [
                <td key={`${column.audience}-surprise`}>{moment && percent(moment.surprise)}</td>,
                <td key={`${column.audience}-tension`}>{moment && percent(moment.tension)}</td>,
              ];
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
