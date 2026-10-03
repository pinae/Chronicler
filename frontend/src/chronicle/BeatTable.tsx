import type { BeatSummary } from "../api/types";

export function BeatTable({ beats }: { beats: BeatSummary[] }) {
  if (beats.length === 0) {
    return <p>No beats in this view yet</p>;
  }
  return (
    <table aria-label="Beats">
      <thead>
        <tr>
          <th scope="col">t</th>
          <th scope="col">Predicate</th>
          <th scope="col">Beat</th>
        </tr>
      </thead>
      <tbody>
        {beats.map((beat) => (
          <tr key={beat.t}>
            <td>{beat.t}</td>
            <td>
              {beat.pred}
              {beat.quarantined && " (quarantined)"}
            </td>
            <td>{beat.text}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
