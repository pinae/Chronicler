import { useEffect, useState } from "react";

import { ApiError, getJson } from "./client";

export type ApiState<T> =
  { status: "loading" } | { status: "error"; notFound: boolean } | { status: "ready"; data: T };

/** Loads JSON from the backend; a new path starts a new load. */
export function useApi<T>(path: string): ApiState<T> {
  const [result, setResult] = useState<{ path: string; state: ApiState<T> } | null>(null);

  useEffect(() => {
    let cancelled = false;
    getJson<T>(path).then(
      (data) => !cancelled && setResult({ path, state: { status: "ready", data } }),
      (error: unknown) =>
        !cancelled &&
        setResult({
          path,
          state: { status: "error", notFound: error instanceof ApiError && error.status === 404 },
        }),
    );
    return () => {
      cancelled = true;
    };
  }, [path]);

  return result?.path === path ? result.state : { status: "loading" };
}
