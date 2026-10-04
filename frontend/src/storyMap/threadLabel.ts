import type { RiverThread } from "../api/types";
import { bindingText } from "../lattice/bindingText";

/** "Hidden crime: C = Judge Adam, V = Frau Marthe, I = ?" */
export function threadLabel(thread: RiverThread): string {
  return `${thread.schema_name}: ${bindingText(thread)}`;
}

export function percent(share: number): string {
  return `${Math.round(share * 100)}%`;
}
