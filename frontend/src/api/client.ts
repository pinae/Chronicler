export class ApiError extends Error {
  readonly status: number;
  /** The backend's explanation, when it gave one. */
  readonly detail: string | null;

  constructor(method: string, path: string, status: number, detail: string | null = null) {
    super(`${method} ${path} answered ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new ApiError("GET", path, response.status);
  }
  return (await response.json()) as T;
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new ApiError("POST", path, response.status, await detailOf(response));
  }
  return (await response.json()) as T;
}

async function detailOf(response: Response): Promise<string | null> {
  try {
    const body: unknown = await response.json();
    return hasTextDetail(body) ? body.detail : null;
  } catch {
    return null;
  }
}

function hasTextDetail(body: unknown): body is { detail: string } {
  return typeof body === "object" && body !== null && "detail" in body && typeof body.detail === "string";
}
