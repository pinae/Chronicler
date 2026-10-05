import type { ReactNode } from "react";

import styles from "./MapColumn.module.css";

/** One audience's column beside the beats, headed by its name in the row of the beats' header. */
export function MapColumn({ name, children }: { name: string; children: ReactNode }) {
  return (
    <div className={styles.column}>
      <div className={styles.columnName}>{name}</div>
      {children}
    </div>
  );
}
