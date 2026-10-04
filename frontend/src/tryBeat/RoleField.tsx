import type { EntitySummary, Role } from "../api/types";
import { fieldKindOf } from "./candidateArgs";

type Props = {
  role: Role;
  entities: EntitySummary[];
  value: string;
  onChange: (value: string) => void;
};

/** One role of the chosen predicate, filled with an entity of the chronicle, a beat's t or a plain
 * value, depending on what the role accepts. */
export function RoleField({ role, entities, value, onChange }: Props) {
  const kind = fieldKindOf(role);
  if (kind === null) {
    return <p>{role.name}: only a proposition fits here, which this form cannot compose.</p>;
  }
  const qualifiers = [kind === "beat" ? "beat t" : null, role.optional ? "optional" : null].filter(Boolean);
  const label = qualifiers.length > 0 ? `${role.name} (${qualifiers.join(", ")})` : role.name;

  if (kind === "entity") {
    return (
      <label>
        {label}{" "}
        <select value={value} onChange={(event) => onChange(event.target.value)}>
          <option value="">—</option>
          {entities.map((entity) => (
            <option key={entity.id} value={String(entity.id)}>
              {entity.name}
            </option>
          ))}
        </select>
      </label>
    );
  }
  return (
    <label>
      {label}{" "}
      <input
        type={kind === "beat" ? "number" : "text"}
        min={kind === "beat" ? 1 : undefined}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}
