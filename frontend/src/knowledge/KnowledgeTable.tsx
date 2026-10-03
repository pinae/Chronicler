import type { KnownBeat } from "../api/types";

type Props = {
  beats: KnownBeat[];
  knowerIsPlayer: boolean;
};

export function KnowledgeTable({ beats, knowerIsPlayer }: Props) {
  if (beats.length === 0) {
    return <p>Nothing known yet</p>;
  }
  return (
    <table aria-label="Known beats">
      <thead>
        <tr>
          <th scope="col">t</th>
          <th scope="col">Beat</th>
          <th scope="col">How</th>
        </tr>
      </thead>
      <tbody>
        {beats.map((beat) => (
          <tr key={beat.t}>
            <td>{beat.t}</td>
            <td>{beat.text}</td>
            <td>{howKnown(beat, knowerIsPlayer)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function howKnown(beat: KnownBeat, knowerIsPlayer: boolean): string {
  if (beat.learned_via_t !== null) {
    return `learned at t = ${beat.learned_via_t}`;
  }
  return knowerIsPlayer ? "saw it" : "present";
}
