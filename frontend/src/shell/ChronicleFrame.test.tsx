import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";

import { ChronicleFrame } from "./ChronicleFrame";

const STEWARD = { id: 2, title: "The Steward of Wend" };

function showFrame(current: "map" | "beats" | "lattice" | "knowledge" | "try") {
  render(
    <MemoryRouter>
      <ChronicleFrame chronicle={STEWARD} current={current}>
        <p>The screen</p>
      </ChronicleFrame>
    </MemoryRouter>,
  );
}

describe("ChronicleFrame", () => {
  it("links every screen of the chronicle", () => {
    showFrame("beats");

    const nav = screen.getByRole("navigation", { name: "Chronicle" });
    const links = within(nav).getAllByRole("link");
    expect(links.map((link) => [link.textContent, link.getAttribute("href")])).toEqual([
      ["Story map", "/chronicles/2/map"],
      ["Beats", "/chronicles/2"],
      ["Lattice", "/chronicles/2/lattice"],
      ["Who knows what", "/chronicles/2/knowledge"],
      ["Try a beat", "/chronicles/2/try"],
    ]);
    expect(screen.getByText("The screen")).toBeInTheDocument();
  });

  it("marks the current screen", () => {
    showFrame("lattice");

    const nav = screen.getByRole("navigation", { name: "Chronicle" });
    expect(within(nav).getByRole("link", { name: "Lattice" })).toHaveAttribute("aria-current", "page");
    expect(within(nav).getByRole("link", { name: "Beats" })).not.toHaveAttribute("aria-current");
  });

  it("leads back to all chronicles", () => {
    showFrame("try");

    const trail = screen.getByRole("navigation", { name: "Breadcrumb" });
    expect(within(trail).getByRole("link", { name: "All chronicles" })).toHaveAttribute("href", "/");
    expect(within(trail).getByText("The Steward of Wend")).toBeInTheDocument();
  });
});
