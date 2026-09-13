import type { Graph, RegistrySnapshot } from "./store";

/** flow/0.1 document shape (GET /api/flows/{name} and PUT body). */
export interface FlowDocument {
  schema: "flow/0.1";
  meta: { name: string };
  graph: Graph;
}

/** Pull the payload out; 400 uses {"errors": [...]}, 404/409 {"detail"}. */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      /* non-JSON error body */
    }
    throw new Error(formatApiError(res.status, res.statusText, path, body));
  }
  return (await res.json()) as T;
}

/** Human-readable message from the two backend error shapes. */
export function formatApiError(
  status: number,
  statusText: string,
  path: string,
  body: unknown,
): string {
  const rec = body as Record<string, unknown> | null;
  if (rec && Array.isArray(rec.errors) && rec.errors.length > 0) {
    return rec.errors.map(String).join("; ");
  }
  if (rec && typeof rec.detail === "string" && rec.detail.length > 0) {
    return rec.detail;
  }
  return status + " " + statusText + ": " + path;
}

/** Error message from a caught unknown (fetch/network or request error). */
export function errorMessage(e: unknown): string {
  return e instanceof Error ? e.message : String(e);
}

export const api = {
  getNodes: () => request<RegistrySnapshot>("/api/nodes"),
  getFlows: () => request<string[]>("/api/flows"),
  getFlow: (name: string) => request<FlowDocument>("/api/flows/" + encodeURIComponent(name)),
  saveFlow: (name: string, doc: FlowDocument) =>
    request<{ ok: true; name: string }>("/api/flows/" + encodeURIComponent(name), {
      method: "PUT",
      body: JSON.stringify(doc),
    }),
  validateFlow: (doc: FlowDocument) =>
    request<{ ok: boolean; errors: string[] }>("/api/validate", {
      method: "POST",
      body: JSON.stringify(doc),
    }),
  runFlow: (name: string) =>
    request<{ ok: true; pid: number }>("/api/run", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),
  runStatus: () => request<unknown>("/api/run/status"),
  runStop: () => request<{ ok: true; stop_flag: string }>("/api/run/stop", { method: "POST" }),
};
