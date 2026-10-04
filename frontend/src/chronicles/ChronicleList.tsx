import { Link } from "react-router";

import type { ChronicleSummary } from "../api/types";
import styles from "./ChronicleList.module.css";

export function ChronicleList({ chronicles }: { chronicles: ChronicleSummary[] }) {
  if (chronicles.length === 0) {
    return <p>No chronicles yet</p>;
  }
  return (
    <ul className={styles.shelf}>
      {chronicles.map((chronicle) => (
        <li key={chronicle.id} className={styles.volume}>
          <Link to={`/chronicles/${chronicle.id}`} className={styles.title}>
            {chronicle.title}
          </Link>{" "}
          <span className={styles.facts}>
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
