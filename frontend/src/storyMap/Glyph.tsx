/** Event marks, in ink with a surface ring so they read on any band (dataviz: 2px surface ring). */
export function GlyphMark({ kind, x, y }: { kind: string; x: number; y: number }) {
  const common = { stroke: "var(--surface-panel)", strokeWidth: 2, paintOrder: "stroke" as const };
  switch (kind) {
    case "completed":
      return <path d={starPath(x, y, 6, 2.6)} fill="var(--ink)" {...common} />;
    case "refuted":
      return (
        <g>
          <path d={crossPath(x, y, 4)} stroke="var(--surface-panel)" strokeWidth={5} strokeLinecap="round" />
          <path d={crossPath(x, y, 4)} stroke="var(--ink)" strokeWidth={2} strokeLinecap="round" />
        </g>
      );
    case "voiced":
      return (
        <path d={`M${x} ${y - 5}L${x + 5} ${y}L${x} ${y + 5}L${x - 5} ${y}Z`} fill="var(--ink)" {...common} />
      );
    default:
      return <circle cx={x} cy={y} r={3.5} fill="var(--ink)" {...common} />;
  }
}

function starPath(x: number, y: number, outer: number, inner: number): string {
  const corners = Array.from({ length: 10 }, (_, index) => {
    const radius = index % 2 === 0 ? outer : inner;
    const angle = (Math.PI / 5) * index - Math.PI / 2;
    return `${(x + radius * Math.cos(angle)).toFixed(2)} ${(y + radius * Math.sin(angle)).toFixed(2)}`;
  });
  return `M${corners.join("L")}Z`;
}

function crossPath(x: number, y: number, size: number): string {
  return `M${x - size} ${y - size}L${x + size} ${y + size}M${x + size} ${y - size}L${x - size} ${y + size}`;
}
