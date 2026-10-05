import { area, curveMonotoneY } from "d3-shape";

import type { RiverColumn } from "../api/types";
import { rowCenter } from "./riverLayout";

/** The tension down the beats as an area growing from the left edge, flowing smoothly from row to row
 * and filling the first and last rows. */
export function tensionPath(column: RiverColumn, width: number, rowHeight: number): string {
  const rows = column.moments.filter((moment) => moment.t > 0);
  const first = rows[0];
  const last = rows.at(-1);
  if (!first || !last) {
    return "";
  }
  const points = [
    { y: 0, x: first.tension * width },
    ...rows.map((moment) => ({ y: rowCenter(moment.t, rowHeight), x: moment.tension * width })),
    { y: last.t * rowHeight, x: last.tension * width },
  ];
  const shape = area<(typeof points)[number]>()
    .y((point) => point.y)
    .x0(0)
    .x1((point) => point.x)
    .curve(curveMonotoneY);
  return shape(points) ?? "";
}
