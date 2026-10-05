import type { ReactNode } from "react";

import styles from "./MapToolbar.module.css";

type Props = {
  legend: ReactNode;
  asTable: boolean;
  onToggle: () => void;
  /** What the button calls the chart: "river", "map". */
  chartName: string;
};

/** A view's legend and the switch between its chart and the tables with the same numbers. */
export function MapToolbar({ legend, asTable, onToggle, chartName }: Props) {
  return (
    <div className={styles.toolbar}>
      {legend}
      <button type="button" onClick={onToggle}>
        {asTable ? `Show as ${chartName}` : "Show as table"}
      </button>
    </div>
  );
}
