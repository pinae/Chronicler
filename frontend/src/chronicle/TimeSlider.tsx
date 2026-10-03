type Props = {
  t: number;
  lastT: number;
  onChange: (t: number) => void;
};

/** Moves the view back and forth in story time: the state after beat t. */
export function TimeSlider({ t, lastT, onChange }: Props) {
  return (
    <label>
      Up to beat{" "}
      <input
        type="range"
        min={0}
        max={lastT}
        value={t}
        onChange={(event) => onChange(Number(event.target.value))}
      />{" "}
      <output>
        t = {t} of {lastT}
      </output>
    </label>
  );
}
