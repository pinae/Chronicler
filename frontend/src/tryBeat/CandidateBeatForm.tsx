import { useState, type FormEvent } from "react";

import type { CandidateBeat, ChronicleDetail, EntitySummary, Predicate } from "../api/types";
import { ALL_BEATS, AudienceSelect } from "../chronicle/AudienceSelect";
import { argsOf } from "./candidateArgs";
import { IdCheckboxes } from "./IdCheckboxes";
import { RoleField } from "./RoleField";

type Props = {
  vocabulary: Predicate[];
  entities: EntitySummary[];
  players: ChronicleDetail["players"];
  running: boolean;
  onTry: (candidate: CandidateBeat) => void;
};

export function CandidateBeatForm({ vocabulary, entities, players, running, onTry }: Props) {
  const [predicateName, setPredicateName] = useState("");
  const [roleValues, setRoleValues] = useState<Record<string, string>>({});
  const [present, setPresent] = useState<number[]>([]);
  const [shownTo, setShownTo] = useState<number[]>(players.map((player) => player.id));
  const [audience, setAudience] = useState(ALL_BEATS);
  const predicate = vocabulary.find((candidate) => candidate.name === predicateName);

  function choosePredicate(name: string) {
    setPredicateName(name);
    setRoleValues({});
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    onTry({
      pred: predicateName,
      args: predicate ? argsOf(predicate, roleValues) : {},
      characters_present: present,
      players_present: shownTo,
      audience,
    });
  }

  return (
    <form onSubmit={submit}>
      <label>
        Predicate{" "}
        <select value={predicateName} onChange={(event) => choosePredicate(event.target.value)}>
          <option value="">Choose…</option>
          {vocabulary.map((candidate) => (
            <option key={candidate.name} value={candidate.name}>
              {candidate.name}
            </option>
          ))}
        </select>
      </label>
      {predicate?.roles.map((role) => (
        <RoleField
          key={`${predicate.name}-${role.name}`}
          role={role}
          entities={entities}
          value={roleValues[role.name] ?? ""}
          onChange={(value) => setRoleValues({ ...roleValues, [role.name]: value })}
        />
      ))}
      <IdCheckboxes
        legend="Present"
        options={entities.filter((entity) => entity.kind === "character")}
        chosen={present}
        onChange={setPresent}
      />
      <IdCheckboxes legend="Shown to" options={players} chosen={shownTo} onChange={setShownTo} />
      <AudienceSelect
        players={players}
        value={audience}
        onChange={setAudience}
        includeTable={false}
        label="Lattice of"
      />
      <button type="submit" disabled={running}>
        Try it
      </button>
    </form>
  );
}
