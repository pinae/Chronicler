import type { River } from "../api/types";
import { GlyphMark } from "./Glyph";
import styles from "./Legend.module.css";
import { OTHER_COLOR, schemaColor } from "./schemaColors";

const EVENTS = [
  { kind: "filled", label: "A step filled" },
  { kind: "completed", label: "Completed" },
  { kind: "refuted", label: "Refuted" },
  { kind: "voiced", label: "Voiced by a player" },
];

/** What the colours, the hatching and the marks mean (dataviz: a legend for two or more series). */
export function Legend({ river }: { river: River }) {
  const schemas = new Map(
    river.columns.flatMap((column) =>
      column.threads.map((thread) => [thread.schema_slug, thread.schema_name]),
    ),
  );
  return (
    <ul aria-label="Legend" className={styles.legend}>
      {[...schemas].map(([slug, name]) => (
        <li key={slug}>
          <Swatch fill={schemaColor(slug)} />
          {name}
        </li>
      ))}
      <li>
        <Swatch fill={OTHER_COLOR} />
        Other readings
      </li>
      <li>
        <Swatch fill={OTHER_COLOR} hatched />
        Only the game master holds it
      </li>
      {EVENTS.map((event) => (
        <li key={event.kind}>
          <svg width="16" height="16" aria-hidden="true">
            <rect width="16" height="16" rx="2" fill="var(--surface-sunken)" />
            <GlyphMark kind={event.kind} x={8} y={8} />
          </svg>
          {event.label}
        </li>
      ))}
    </ul>
  );
}

function Swatch({ fill, hatched = false }: { fill: string; hatched?: boolean }) {
  return (
    <svg width="16" height="16" aria-hidden="true">
      <rect width="16" height="16" rx="2" fill={fill} />
      {hatched &&
        [-8, 0, 8].map((offset) => (
          <line
            key={offset}
            x1={offset}
            y1="16"
            x2={offset + 16}
            y2="0"
            stroke="var(--hatch)"
            strokeWidth="2.5"
          />
        ))}
    </svg>
  );
}
