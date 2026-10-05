import styles from "./KnowledgeMarks.module.css";

export const MARK_SIZE = 12;

/** A beat the audience knew when it happened: a filled square centred on (x, y). */
export function KnownMark({ x, y }: { x: number; y: number }) {
  const half = MARK_SIZE / 2;
  return (
    <rect className={styles.known} x={x - half} y={y - half} width={MARK_SIZE} height={MARK_SIZE} rx="1" />
  );
}
