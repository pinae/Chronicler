import type { RiverColumn } from "../api/types";
import styles from "./PacingChart.module.css";
import marks from "./PacingMarks.module.css";
import { tensionPath } from "./pacingLayout";
import { rowCenter } from "./riverLayout";
import { percent } from "./threadLabel";

const BAR_HEIGHT = 10;

type Props = {
  column: RiverColumn;
  width: number;
  rowHeight: number;
  lastT: number;
};

/** One audience's pacing down the beats: tension as an area, surprise as a bar in each beat's row,
 * both from nothing at the left edge to all of the belief at the right (§6 of the research note). */
export function PacingChart({ column, width, rowHeight, lastT }: Props) {
  const height = lastT * rowHeight;
  const rows = column.moments.filter((moment) => moment.t > 0);
  return (
    <svg
      role="img"
      aria-label={`Pacing: ${column.name}`}
      className={styles.chart}
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
    >
      <line className={styles.half} x1={width / 2} y1={0} x2={width / 2} y2={height} />
      <path className={marks.tension} d={tensionPath(column, width, rowHeight)} />
      {rows.map((moment) => (
        <rect
          key={moment.t}
          className={marks.surprise}
          x={0}
          y={rowCenter(moment.t, rowHeight) - BAR_HEIGHT / 2}
          width={moment.surprise * width}
          height={BAR_HEIGHT}
        />
      ))}
      {rows.map((moment) => (
        <rect
          key={moment.t}
          className={styles.row}
          x={0}
          y={(moment.t - 1) * rowHeight}
          width={width}
          height={rowHeight}
        >
          <title>
            {`t = ${moment.t}, ${column.name}: surprise ${percent(moment.surprise)}, tension ${percent(moment.tension)}`}
          </title>
        </rect>
      ))}
    </svg>
  );
}
