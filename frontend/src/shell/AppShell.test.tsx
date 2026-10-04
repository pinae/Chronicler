import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it } from "vitest";

import { AppShell } from "./AppShell";

function showShell() {
  return render(
    <MemoryRouter>
      <AppShell>
        <p>The page</p>
      </AppShell>
    </MemoryRouter>,
  );
}

afterEach(() => {
  localStorage.clear();
  delete document.documentElement.dataset.theme;
});

describe("AppShell", () => {
  it("shows the brand linking to the chronicle list above the page", () => {
    showShell();

    const banner = screen.getByRole("banner");
    expect(within(banner).getByRole("link", { name: "Chronicler" })).toHaveAttribute("href", "/");
    expect(screen.getByText("The page")).toBeInTheDocument();
  });

  it("follows the system theme until a theme is chosen", () => {
    showShell();

    expect(screen.getByLabelText("Theme")).toHaveValue("system");
    expect(document.documentElement.dataset.theme).toBeUndefined();
  });

  it("applies and remembers the chosen theme", async () => {
    const { unmount } = showShell();

    await userEvent.selectOptions(screen.getByLabelText("Theme"), "Dark");
    expect(document.documentElement.dataset.theme).toBe("dark");

    unmount();
    delete document.documentElement.dataset.theme;
    showShell();

    expect(screen.getByLabelText("Theme")).toHaveValue("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("hands the choice back to the system", async () => {
    showShell();
    await userEvent.selectOptions(screen.getByLabelText("Theme"), "Light");

    await userEvent.selectOptions(screen.getByLabelText("Theme"), "System");

    expect(document.documentElement.dataset.theme).toBeUndefined();
    expect(localStorage.getItem("chronicler-theme")).toBeNull();
  });
});
