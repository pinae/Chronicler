type Option = { id: number; name: string };

type Props = {
  legend: string;
  options: Option[];
  chosen: number[];
  onChange: (chosen: number[]) => void;
};

/** A group of checkboxes choosing some of the options, by id. */
export function IdCheckboxes({ legend, options, chosen, onChange }: Props) {
  function toggle(id: number) {
    onChange(chosen.includes(id) ? chosen.filter((other) => other !== id) : [...chosen, id]);
  }

  return (
    <fieldset>
      <legend>{legend}</legend>
      {options.map((option) => (
        <label key={option.id}>
          <input type="checkbox" checked={chosen.includes(option.id)} onChange={() => toggle(option.id)} />
          {option.name}
        </label>
      ))}
    </fieldset>
  );
}
