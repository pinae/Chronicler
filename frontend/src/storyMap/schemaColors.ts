/** Colour means schema (ADR-011): a fixed map, so a schema keeps its colour on every screen. */
const SCHEMA_COLORS: Record<string, string> = {
  betrayal: "var(--schema-betrayal)",
  usurpation: "var(--schema-usurpation)",
  blame: "var(--schema-blame)",
  hidden_crime: "var(--schema-hidden-crime)",
  prophecy: "var(--schema-prophecy)",
};

export const OTHER_COLOR = "var(--schema-other)";

export function schemaColor(schemaSlug: string | null): string {
  return (schemaSlug && SCHEMA_COLORS[schemaSlug]) || OTHER_COLOR;
}
