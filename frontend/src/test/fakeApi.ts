import { vi } from "vitest";

type Routes = Record<string, unknown>;

/** Replaces fetch: each path answers with its JSON body; unknown paths answer 404. */
export function fakeApi(routes: Routes): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const path = String(input);
      if (!(path in routes)) {
        return new Response(JSON.stringify({ detail: "Not Found" }), { status: 404 });
      }
      return new Response(JSON.stringify(routes[path]), { status: 200 });
    }),
  );
}

/** Replaces fetch with one that always fails, as when the backend is down. */
export function unreachableApi(): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response("Bad Gateway", { status: 502 })),
  );
}
