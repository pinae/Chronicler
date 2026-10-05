import styles from "./KnowledgeMarks.module.css";
import { MARK_SIZE } from "./KnownMark";

type Props = {
  /** The centre of the beat's square, in the row where it happened. */
  x: number;
  y: number;
  /** The fuse's lane and the row where the beat was learned. */
  laneX: number;
  learnedY: number;
};

/** A beat learned later: a hollow square in its own row and a fuse burning down to where it was
 * learned, ending in a spark. */
export function FuseMark({ x, y, laneX, learnedY }: Props) {
  const half = MARK_SIZE / 2;
  const cord = `M${x + half} ${y}H${laneX}V${learnedY}`;
  return (
    <>
      <path d={cord} stroke="transparent" strokeWidth="10" fill="none" />
      <path d={cord} className={styles.cord} />
      <rect
        className={styles.learned}
        x={x - half}
        y={y - half}
        width={MARK_SIZE}
        height={MARK_SIZE}
        rx="1"
      />
      <circle className={styles.spark} cx={laneX} cy={learnedY} r="4" />
    </>
  );
}
