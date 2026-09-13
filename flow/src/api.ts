import type { Graph, RunStatus } from "./store";

export interface FlowSpec {
  id: string;
  name: string;
  graph: Graph;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}: ${path}`);
  return res.json() as Promise<T>;
}

export const api = {
  getNodes: () => request<unknown[]>("/api/nodes"),
  getFlows: () => request<FlowSpec[]>("/api/flows"),
  saveFlow: (flow: FlowSpec) =>
    request<{ ok: true }>("/api/flows", {
      method: "POST",
      body: JSON.stringify(flow),
    }),
  validateFlow: (graph: Graph) =>
    request<{ valid: boolean; errors: string[] }>("/api/validate", {
      method: "POST",
      body: JSON.stringify({ graph }),
    }),
  runFlow: (id: string) =>
    request<{ runId: string }>("/api/run", {
      method: "POST",
      body: JSON.stringify({ id }),
    }),
  runStatus: (runId: string) => request<RunStatus>(`/api/run/${runId}`),
  runStop: (runId: string) =>
    request<{ ok: true }>(`/api/run/${runId}/stop`, { method: "POST" }),
};
