import { Link } from "react-router";

import type { ChronicleSummary } from "../api/types";

export function ChronicleList({ chronicles }: { chronicles: ChronicleSummary[] }) {
  if (chronicles.length === 0) {
    return <p>No chronicles yet</p>;
  }
  return (
    <ul>
      {chronicles.map((chronicle) => (
        <li key={chronicle.id}>
          <Link to={`/chronicles/${chronicle.id}`}>{chronicle.title}</Link>{" "}
          <span>
            {chronicle.kind} · {beatCount(chronicle.beat_count)}
          </span>
        </li>
      ))}
    </ul>
  );
}

function beatCount(count: number): string {
  return count === 1 ? "1 beat" : `${count} beats`;
}
