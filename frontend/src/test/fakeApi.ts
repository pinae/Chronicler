import { vi } from "vitest";

type Routes = Record<string, unknown>;
type PostHandler = (body: unknown) => { status: number; body: unknown };

/** Replaces fetch: each GET path answers with its JSON body, each POST path with what its handler
 * returns for the request body; unknown paths answer 404. */
export function fakeApi(routes: Routes, posts: Record<string, PostHandler> = {}): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = String(input);
      if (init?.method === "POST") {
        return answerPost(posts[path], init.body);
      }
      if (!(path in routes)) {
        return notFound();
      }
      return new Response(JSON.stringify(routes[path]), { status: 200 });
    }),
  );
}

function answerPost(handler: PostHandler | undefined, body: RequestInit["body"]): Response {
  if (handler === undefined) {
    return notFound();
  }
  const answer = handler(JSON.parse(String(body)));
  return new Response(JSON.stringify(answer.body), { status: answer.status });
}

function notFound(): Response {
  return new Response(JSON.stringify({ detail: "Not Found" }), { status: 404 });
}

/** Replaces fetch with one that always fails, as when the backend is down. */
export function unreachableApi(): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response("Bad Gateway", { status: 502 })),
  );
}
