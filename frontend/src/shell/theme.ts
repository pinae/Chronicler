export type ThemeChoice = "system" | "light" | "dark";

const STORAGE_KEY = "chronicler-theme";

/** The theme the viewer chose last; storage may be unavailable (private windows), then "system". */
export function storedTheme(): ThemeChoice {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === "light" || stored === "dark" ? stored : "system";
  } catch {
    return "system";
  }
}

/** Applies the choice to the page (tokens.css reads data-theme) and remembers it. */
export function applyTheme(choice: ThemeChoice): void {
  const root = document.documentElement;
  if (choice === "system") {
    delete root.dataset.theme;
  } else {
    root.dataset.theme = choice;
  }
  remember(choice);
}

function remember(choice: ThemeChoice): void {
  try {
    if (choice === "system") {
      localStorage.removeItem(STORAGE_KEY);
    } else {
      localStorage.setItem(STORAGE_KEY, choice);
    }
  } catch {
    // Without storage the choice lasts for this page only.
  }
}
