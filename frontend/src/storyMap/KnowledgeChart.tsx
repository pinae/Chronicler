import type { KnowledgeColumn } from "../api/types";
import { FuseMark } from "./FuseMark";
import styles from "./KnowledgeChart.module.css";
import { KnownMark, MARK_SIZE } from "./KnownMark";
import { fuses, howKnown } from "./knowledgeLayout";
import { rowCenter } from "./riverLayout";

const MARK_X = 22;
const FIRST_LANE_X = MARK_X + MARK_SIZE + 4;
const LANE_GAP = 9;

type Props = {
  column: KnowledgeColumn;
  width: number;
  rowHeight: number;
  lastT: number;
};

/** One player's knowledge down the beats: a square where they knew a beat when it happened, a fuse
 * from a beat down to where they learned it, nothing where they never did (dataviz: the story curve
 * of a session, in the story map's rows). */
export function KnowledgeChart({ column, width, rowHeight, lastT }: Props) {
  const height = lastT * rowHeight;
  const fuseOf = new Map(fuses(column).map((fuse) => [fuse.t, fuse]));
  const lanes = Math.max(0, ...[...fuseOf.values()].map((fuse) => fuse.lane + 1));
  const laneGap = lanes > 1 ? Math.min(LANE_GAP, (width - FIRST_LANE_X - 4) / (lanes - 1)) : 0;

  return (
    <svg
      role="img"
      aria-label={`Knowledge of ${column.name}`}
      className={styles.chart}
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
    >
      {column.known.map((cell) => {
        const y = rowCenter(cell.t, rowHeight);
        const fuse = fuseOf.get(cell.t);
        return (
          <g key={cell.t} className={styles.mark} data-testid={fuse ? `fuse-${cell.t}` : undefined}>
            <title>{`Beat ${cell.t}, ${column.name}: ${howKnown(cell)}`}</title>
            {fuse ? (
              <FuseMark
                x={MARK_X}
                y={y}
                laneX={FIRST_LANE_X + fuse.lane * laneGap}
                learnedY={rowCenter(fuse.knownSinceT, rowHeight)}
              />
            ) : (
              <KnownMark x={MARK_X} y={y} />
            )}
          </g>
        );
      })}
    </svg>
  );
}
