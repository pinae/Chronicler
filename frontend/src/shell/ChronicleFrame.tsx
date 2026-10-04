import type { ReactNode } from "react";
import { Link } from "react-router";

import styles from "./ChronicleFrame.module.css";

export type ChronicleScreen = "beats" | "lattice" | "knowledge" | "try";

const SCREENS: { screen: ChronicleScreen; label: string; path: string }[] = [
  { screen: "beats", label: "Beats", path: "" },
  { screen: "lattice", label: "Lattice", path: "/lattice" },
  { screen: "knowledge", label: "Who knows what", path: "/knowledge" },
  { screen: "try", label: "Try a beat", path: "/try" },
];

type Props = {
  chronicle: { id: number; title: string };
  current: ChronicleScreen;
  children: ReactNode;
};

/** A chronicle's screens share a breadcrumb and a navigation with the current screen marked. */
export function ChronicleFrame({ chronicle, current, children }: Props) {
  return (
    <main className={styles.frame}>
      <nav aria-label="Breadcrumb" className={styles.breadcrumb}>
        <Link to="/">All chronicles</Link>
        <span aria-hidden="true"> › </span>
        <span>{chronicle.title}</span>
      </nav>
      <nav aria-label="Chronicle" className={styles.tabs}>
        {SCREENS.map(({ screen, label, path }) => (
          <Link
            key={screen}
            to={`/chronicles/${chronicle.id}${path}`}
            className={styles.tab}
            aria-current={screen === current ? "page" : undefined}
          >
            {label}
          </Link>
        ))}
      </nav>
      <div className={styles.screen}>{children}</div>
    </main>
  );
}
