import { useEffect, useState } from "react";

import styles from "./ThemeSwitch.module.css";
import { applyTheme, storedTheme, type ThemeChoice } from "./theme";

export function ThemeSwitch() {
  const [choice, setChoice] = useState<ThemeChoice>(storedTheme);

  useEffect(() => {
    applyTheme(choice);
  }, [choice]);

  return (
    <label className={styles.switch}>
      Theme{" "}
      <select value={choice} onChange={(event) => setChoice(event.target.value as ThemeChoice)}>
        <option value="system">System</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </label>
  );
}
