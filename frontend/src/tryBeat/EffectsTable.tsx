import type { Effect } from "../api/types";
import { bindingText } from "../lattice/bindingText";

type Props = {
  effects: Effect[];
};

export function EffectsTable({ effects }: Props) {
  if (effects.length === 0) {
    return <p>No hypothesis would change.</p>;
  }
  return (
    <table aria-label="Effects">
      <thead>
        <tr>
          <th scope="col">Hypothesis</th>
          <th scope="col">Change</th>
          <th scope="col">Weight</th>
        </tr>
      </thead>
      <tbody>
        {effects.map((effect, index) => (
          <tr key={`${effect.hypothesis_id ?? "new"}-${index}`}>
            <td>
              {effect.schema_name}: {bindingText(effect)}
            </td>
            <td>{changeText(effect)}</td>
            <td>{weightText(effect)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** "filled reveal, completed", "seeded (trust)", "refuted". */
function changeText(effect: Effect): string {
  return effect.changes
    .map((change) => {
      if (change === "filled") {
        return `filled ${effect.filled_step}`;
      }
      if ((change === "seeded" || change === "refined") && effect.filled_step !== null) {
        return `${change} (${effect.filled_step})`;
      }
      return change;
    })
    .join(", ");
}

/** "0.0 → 1.5" for a hypothesis that exists, "new: -1.5" for one the beat would create. */
function weightText(effect: Effect): string {
  const after = effect.weight_after.toFixed(1);
  return effect.weight_before === null ? `new: ${after}` : `${effect.weight_before.toFixed(1)} → ${after}`;
}
