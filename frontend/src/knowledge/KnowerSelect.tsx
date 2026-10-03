import type { ChronicleDetail, EntitySummary } from "../api/types";

type Props = {
  characters: EntitySummary[];
  players: ChronicleDetail["players"];
  value: string;
  onChange: (knower: string) => void;
};

/** A knower is a character in the story ("character-11") or a player at the table ("player-8"). */
export function KnowerSelect({ characters, players, value, onChange }: Props) {
  return (
    <label>
      Who{" "}
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Choose…</option>
        <optgroup label="Characters">
          {characters.map((character) => (
            <option key={character.id} value={`character-${character.id}`}>
              {character.name}
            </option>
          ))}
        </optgroup>
        <optgroup label="Players">
          {players.map((player) => (
            <option key={player.id} value={`player-${player.id}`}>
              {player.name}
            </option>
          ))}
        </optgroup>
      </select>
    </label>
  );
}
