import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";

import { fakeApi, unreachableApi } from "../test/fakeApi";
import { ChroniclesPage } from "./ChroniclesPage";

function showPage() {
  render(
    <MemoryRouter>
      <ChroniclesPage />
    </MemoryRouter>,
  );
}

describe("ChroniclesPage", () => {
  it("lists every chronicle with its kind and number of beats", async () => {
    fakeApi({
      "/api/chronicles/": [
        { id: 2, title: "The Steward of Wend", kind: "session", beat_count: 24 },
        { id: 1, title: "The Count of Monte Cristo", kind: "literature", beat_count: 1 },
      ],
    });

    showPage();

    expect(screen.getByRole("heading", { name: "Chronicles" })).toBeInTheDocument();
    const steward = await screen.findByRole("link", { name: "The Steward of Wend" });
    expect(steward).toHaveAttribute("href", "/chronicles/2");
    expect(screen.getByText("session · 24 beats")).toBeInTheDocument();
    expect(screen.getByText("literature · 1 beat")).toBeInTheDocument();
  });

  it("says so when there are no chronicles yet", async () => {
    fakeApi({ "/api/chronicles/": [] });

    showPage();

    expect(await screen.findByText("No chronicles yet")).toBeInTheDocument();
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
  });

  it("explains when the chronicles cannot be loaded", async () => {
    unreachableApi();

    showPage();

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load the chronicles.");
  });
});
