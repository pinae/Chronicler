import type { RiverColumn, RiverThread } from "../api/types";
import styles from "./ArcLane.module.css";
import { threadArcs } from "./arcLayout";
import { schemaColor } from "./schemaColors";
import { threadLabel } from "./threadLabel";

type Props = {
  selected: { column: RiverColumn; thread: RiverThread } | null;
  width: number;
  rowHeight: number;
  lastT: number;
};

/** The steps of the selected thread as arcs between the beats that filled them (Shape of Song). */
export function ArcLane({ selected, width, rowHeight, lastT }: Props) {
  const height = lastT * rowHeight;
  if (selected === null) {
    return (
      <div className={styles.lane} style={{ width, height }}>
        <p className={styles.hint}>Click a band to see its steps</p>
      </div>
    );
  }
  const { column, thread } = selected;
  const edge = width - 4;
  const { points, arcs, toCome } = threadArcs(column, thread, rowHeight, edge, lastT);
  const color = schemaColor(thread.schema_slug);
  return (
    <div className={styles.lane} style={{ width, height }}>
      <svg
        role="img"
        aria-label={`Steps of ${threadLabel(thread)} (${column.name})`}
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
      >
        {arcs.map((arc) => (
          <path key={`${arc.from.t}-${arc.to.t}`} d={arc.path} fill="none" stroke={color} strokeWidth="2" />
        ))}
        {toCome && (
          <g>
            <line
              x1={edge}
              y1={toCome.y1}
              x2={edge}
              y2={toCome.y2}
              stroke={color}
              strokeWidth="2"
              strokeDasharray="4 4"
            />
            <text x={edge - 6} y={toCome.y2 - 6} textAnchor="end" className={styles.toCome}>
              to come: {toCome.steps.join(", ")}
            </text>
          </g>
        )}
        {points.map((point) => (
          <g key={point.t}>
            <circle
              cx={edge}
              cy={point.y}
              r="4"
              fill={color}
              stroke="var(--surface-panel)"
              strokeWidth="2"
              paintOrder="stroke"
            />
            <text x={edge - 8} y={point.y + 4} textAnchor="end" className={styles.step}>
              {point.steps.join(", ")}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
