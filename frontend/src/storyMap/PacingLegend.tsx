import styles from "./Legend.module.css";
import marks from "./PacingMarks.module.css";

/** What the pacing chart's area and bars mean. */
export function PacingLegend() {
  return (
    <ul aria-label="Legend" className={styles.legend}>
      <li>
        <svg width="16" height="16" aria-hidden="true">
          <path className={marks.tension} d="M0 0H6C12 4 12 12 10 16H0Z" />
        </svg>
        Tension: belief in stories building towards a payoff
      </li>
      <li>
        <svg width="16" height="16" aria-hidden="true">
          <rect className={marks.surprise} x="0" y="3" width="14" height="10" />
        </svg>
        Surprise: how much belief moved at this beat
      </li>
    </ul>
  );
}
