import { FuseMark } from "./FuseMark";
import { KnownMark } from "./KnownMark";
import styles from "./Legend.module.css";

/** What the knowledge map's marks mean. */
export function KnowledgeLegend() {
  return (
    <ul aria-label="Legend" className={styles.legend}>
      <li>
        <svg width="16" height="16" aria-hidden="true">
          <KnownMark x={8} y={8} />
        </svg>
        Knew it when it happened
      </li>
      <li>
        <svg width="34" height="24" aria-hidden="true">
          <FuseMark x={8} y={7} laneX={26} learnedY={18} />
        </svg>
        Learned it later, where the fuse ends
      </li>
      <li>
        <svg width="16" height="16" aria-hidden="true">
          <rect width="16" height="16" rx="2" fill="none" stroke="var(--rule)" strokeDasharray="2 2" />
        </svg>
        Never learned it
      </li>
    </ul>
  );
}
