import type { ChronicleDetail } from "../api/types";

export const ALL_BEATS = "all";
export const TABLE = "table";

type Props = {
  players: ChronicleDetail["players"];
  value: string;
  onChange: (audience: string) => void;
};

/** Whose view to show: every beat (the GM's), the table's common knowledge, or one player's. */
export function AudienceSelect({ players, value, onChange }: Props) {
  return (
    <label>
      Seen by{" "}
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value={ALL_BEATS}>All beats</option>
        <option value={TABLE}>The table</option>
        {players.map((player) => (
          <option key={player.id} value={String(player.id)}>
            {player.name}
          </option>
        ))}
      </select>
    </label>
  );
}
