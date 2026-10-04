import { useId, useState, type PointerEvent } from "react";

import type { RiverColumn, RiverThread } from "../api/types";
import { compatible } from "./compatible";
import { GlyphMark } from "./Glyph";
import styles from "./RiverChart.module.css";
import { OTHER, bandLayouts, bandPath, glyphs, secretRows, type Band, type Glyph } from "./riverLayout";
import { schemaColor } from "./schemaColors";
import { percent, threadLabel } from "./threadLabel";

type Props = {
  column: RiverColumn;
  width: number;
  rowHeight: number;
  /** The thread pointed at in any column; bands that cannot be the same story are dimmed. */
  highlighted: RiverThread | null;
  onHighlight: (thread: RiverThread | null) => void;
};

type Pointed = { band: Band; t: number; y: number };

/** One audience's story river: its threads as bands down the beats, hatched where secret. */
export function RiverChart({ column, width, rowHeight, highlighted, onHighlight }: Props) {
  const id = useId();
  const [pointed, setPointed] = useState<Pointed | null>(null);
  const bands = bandLayouts(column, width);
  const marks = glyphs(column, bands, rowHeight);
  const lastT = Math.max(0, ...column.moments.map((moment) => moment.t));
  const height = lastT * rowHeight;
  const hatchId = `${id}-hatch`;

  function point(band: Band, event: PointerEvent<SVGPathElement>) {
    const top = event.currentTarget.ownerSVGElement?.getBoundingClientRect().top ?? 0;
    const y = event.clientY - top;
    const t = Math.min(lastT, Math.max(1, Math.floor(y / rowHeight) + 1));
    setPointed({ band, t, y });
    onHighlight(column.threads.find((thread) => thread.id === band.threadId) ?? null);
  }

  function dimmed(band: Band): boolean {
    if (highlighted === null) {
      return false;
    }
    const thread = column.threads.find((candidate) => candidate.id === band.threadId);
    return !thread || !compatible(thread, highlighted);
  }

  return (
    <div className={styles.chart}>
      <svg
        role="img"
        aria-label={`Story river: ${column.name}`}
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        onPointerLeave={() => {
          setPointed(null);
          onHighlight(null);
        }}
      >
        <defs>
          <pattern
            id={hatchId}
            width="6"
            height="6"
            patternUnits="userSpaceOnUse"
            patternTransform="rotate(45)"
          >
            <line x1="0" y1="0" x2="0" y2="6" stroke="var(--hatch)" strokeWidth="2.5" />
          </pattern>
          {bands.map((band) => (
            <clipPath key={band.key} id={`${id}-secret-${band.key}`}>
              {secretRows(band).map((t) => (
                <rect key={t} x="0" y={(t - 1) * rowHeight} width={width} height={rowHeight} />
              ))}
            </clipPath>
          ))}
        </defs>
        {bands.map((band) => {
          const path = bandPath(band, rowHeight);
          return (
            <g key={band.key}>
              <path
                d={path}
                fill={band.key === OTHER ? "var(--schema-other)" : schemaColor(band.schemaSlug)}
                data-testid={`band-${band.key}`}
                data-dimmed={dimmed(band) || undefined}
                className={styles.band}
                onPointerMove={(event) => point(band, event)}
              />
              {secretRows(band).length > 0 && (
                <path
                  d={path}
                  fill={`url(#${hatchId})`}
                  clipPath={`url(#${id}-secret-${band.key})`}
                  pointerEvents="none"
                />
              )}
            </g>
          );
        })}
        {marks.map((mark) => (
          <GlyphMark key={`${mark.threadId}-${mark.t}-${mark.kind}`} kind={mark.kind} x={mark.x} y={mark.y} />
        ))}
      </svg>
      {pointed && <BandTooltip column={column} pointed={pointed} marks={marks} />}
    </div>
  );
}

function BandTooltip({ column, pointed, marks }: { column: RiverColumn; pointed: Pointed; marks: Glyph[] }) {
  const point = pointed.band.points.find((candidate) => candidate.t === pointed.t);
  const thread = column.threads.find((candidate) => candidate.id === pointed.band.threadId);
  const events = marks.filter((mark) => mark.threadId === pointed.band.threadId && mark.t === pointed.t);
  return (
    <div role="tooltip" className={styles.tooltip} style={{ top: pointed.y }}>
      <strong>
        {percent(point?.share ?? 0)} at t = {pointed.t}
      </strong>
      <span>{thread ? threadLabel(thread) : "Other readings"}</span>
      {point?.status && (
        <span className={styles.muted}>
          {point.status}
          {point.secret && " · only the game master holds it"}
        </span>
      )}
      {events.length > 0 && (
        <span className={styles.muted}>This beat: {events.map(eventText).join(", ")}</span>
      )}
    </div>
  );
}

function eventText(event: Glyph): string {
  switch (event.kind) {
    case "filled":
      return `${event.steps.join(", ")} filled`;
    case "voiced":
      return "voiced by a player";
    default:
      return event.kind;
  }
}
