import { Link } from "react-router";

import styles from "./StoryMapViews.module.css";

export type StoryMapViewName = "river" | "knowledge" | "pacing";

const VIEWS: { view: StoryMapViewName; label: string; path: string }[] = [
  { view: "river", label: "Story river", path: "/map" },
  { view: "knowledge", label: "Knowledge map", path: "/map/knowledge" },
  { view: "pacing", label: "Pacing", path: "/map/pacing" },
];

/** The story map's views share the beat rows; this switches between them. */
export function StoryMapViews({ chronicleId, current }: { chronicleId: number; current: StoryMapViewName }) {
  return (
    <nav aria-label="Story map views" className={styles.views}>
      {VIEWS.map(({ view, label, path }) => (
        <Link
          key={view}
          to={`/chronicles/${chronicleId}${path}`}
          className={styles.view}
          aria-current={view === current ? "page" : undefined}
        >
          {label}
        </Link>
      ))}
    </nav>
  );
}
