import { create } from "zustand";
import type { Edge, Node, NodeChange, EdgeChange, Connection } from "@xyflow/react";
import { applyNodeChanges } from "@xyflow/react";

/**
 * Canonical graph shape is the flow/0.1 document graph (what the backend
 * serves/stores). xyflow ReactFlow Node/Edge objects are a projection of
 * this; mappers live at the bottom of this file.
 */
export interface DomainPosition { x: number; y: number }

export interface DomainNode {
  id: string;
  kind: string;
  label?: string;
  props: Record<string, unknown>;
  position: DomainPosition;
}

export interface DomainEdge {
  id: string;
  from: string;
  to: string;
  fromPort: string;
  toPort: string;
}

export interface Graph {
  nodes: DomainNode[];
  edges: DomainEdge[];
}

/** Registry snapshot shape from GET /api/nodes. */
export interface PortSpec {
  name: string;
  direction: "in" | "out";
  type: string;
  "burst-format"?: string | null;
}

export interface NodeSpec {
  ports: PortSpec[];
  props: string[];
  numeric_props: string[];
  gate: string | null;
}

export interface RegistrySnapshot {
  valid_kinds: string[];
  nodes: Record<string, NodeSpec>;
  gates: Record<string, string | null>;
}

/** Static fallback REGISTRY_COPY, used ONLY when GET /api/nodes fails. */
export const FALLBACK_REGISTRY: RegistrySnapshot = {
  valid_kinds: ["dataset", "prepare", "tokenize", "train", "eval", "infer"],
  nodes: {
    dataset: { ports: [{ name: "cleaned", direction: "out", type: "raw-dir" }], props: [], numeric_props: [], gate: null },
    prepare: {
      ports: [
        { name: "raw-dir", direction: "in", type: "raw-dir" },
        { name: "cleaned-dir", direction: "out", type: "cleaned-dir" },
      ],
      props: ["min_chars", "rows", "val_fraction"],
      numeric_props: ["min_chars", "rows", "val_fraction"],
      gate: null,
    },
    tokenize: {
      ports: [
        { name: "cleaned-dir", direction: "in", type: "cleaned-dir" },
        { name: "shard-dir", direction: "out", type: "shard-dir" },
      ],
      props: ["seq_len", "vocab"],
      numeric_props: ["seq_len", "vocab"],
      gate: null,
    },
    train: {
      ports: [
        { name: "shard-dir", direction: "in", type: "shard-dir" },
        { name: "ckpt-dir", direction: "out", type: "ckpt-dir" },
      ],
      props: ["lr_preset", "preset", "steps"],
      numeric_props: ["steps"],
      gate: "gpu",
    },
    eval: {
      ports: [
        { name: "ckpt-dir", direction: "in", type: "ckpt-dir" },
        { name: "report", direction: "out", type: "report" },
      ],
      props: [],
      numeric_props: [],
      gate: "gpu",
    },
    infer: {
      ports: [{ name: "ckpt-dir", direction: "in", type: "ckpt-dir" }],
      props: [],
      numeric_props: [],
      gate: "gpu/cpu",
    },
  },
  gates: { dataset: null, prepare: null, tokenize: null, train: "gpu", eval: "gpu", infer: "gpu/cpu" },
};

export type InspectorTab = "properties" | "run-log" | "preview";

/** UI-level run state; setRunStatus stays unwired until the Task 9/10 run
 * wiring. The raw backend payload type is ApiRunStatus in api.ts
 * (GET /api/run/status contract shape). */
export interface RunStatus {
  state: "idle" | "running" | "done" | "error";
  message?: string;
}

export interface FlowState {
  graph: Graph;
  /** Last xyflow projection (full nodes, incl. measured width/height and
   * dragging/selected flags). toXYNodes merges it back so unchanged
   * domain nodes keep their data identity (PipelineNode is memoized) and
   * geometry/interaction flags persist across the controlled-render
   * round-trip (T8 review IMPORTANT-3). */
  projection: PipelineNode[];
  selection: string | null;
  inspectorTab: InspectorTab;
  runStatus: RunStatus | null;
  paletteCollapsed: boolean;
  inspectorCollapsed: boolean;
  /** Registry snapshot; null until GET /api/nodes resolves. */
  registry: RegistrySnapshot | null;
  /** Set when the registry fetch itself failed (fallback list in use). */
  registryError: string | null;
  /** User-visible error / toast line; reducers never mutate graph on reject. */
  error: string | null;
  setGraph: (g: Graph) => void;
  setSelection: (id: string | null) => void;
  setInspectorTab: (t: InspectorTab) => void;
  setRunStatus: (s: RunStatus | null) => void;
  setPaletteCollapsed: (c: boolean) => void;
  setInspectorCollapsed: (c: boolean) => void;
  setRegistry: (r: RegistrySnapshot) => void;
  setRegistryError: (e: string | null) => void;
  setError: (e: string | null) => void;
  /** Pure, reducer-safe actions (each fully testable via getState()). */
  addNode: (kind: string, position: DomainPosition) => string | null;
  applyNodesChanges: (changes: NodeChange[]) => void;
  applyEdgesChanges: (changes: EdgeChange[]) => void;
  connect: (c: Connection) => boolean;
}

/* ------------------------------------------------------------------ */
/* Pure reducers / mappers - exported for direct unit testing.         */
/* ------------------------------------------------------------------ */

/** Port-type compatibility: exact match or one side is a prefixed
 * description of the other ("raw-dir" vs "raw-dir: dataset name/rows").
 * The dataset node's out port carries a descriptive suffix, so strict
 * string equality would refuse the primary dataset -> prepare edge. */
export function portTypesCompatible(a: string, b: string): boolean {
  const base = (t: string) => t.split(":")[0].trim();
  return base(a) === base(b);
}

/** Deterministic unique id: reuse a simple counter over existing "nK". */
export function nextNodeId(graph: Graph, prefix = "n"): string {
  let max = 0;
  for (const node of graph.nodes) {
    if (!node.id.startsWith(prefix)) continue;
    const rest = node.id.slice(prefix.length);
    if (/^[0-9]+$/.test(rest)) max = Math.max(max, Number(rest));
  }
  return prefix + (max + 1);
}

/** Deterministic unique EDGE id: mirror of nextNodeId over graph.edges.
 * connectReducer used to call nextNodeId(graph, "e"), which only scans
 * graph.nodes, so every new edge got id "e1" (T8 review CRITICAL-1). */
export function nextEdgeId(graph: Graph, prefix = "e"): string {
  let max = 0;
  for (const edge of graph.edges) {
    if (!edge.id.startsWith(prefix)) continue;
    const rest = edge.id.slice(prefix.length);
    if (/^[0-9]+$/.test(rest)) max = Math.max(max, Number(rest));
  }
  return prefix + (max + 1);
}

/** Validate a new edge against the registry snapshot.
 * Returns [] when acceptable, otherwise one human-readable reason. */
export function validateConnect(
  registry: RegistrySnapshot,
  graph: Graph,
  fromId: string,
  toId: string,
  fromPort: string,
  toPort: string,
): string[] {
  const source = graph.nodes.find((n) => n.id === fromId);
  const target = graph.nodes.find((n) => n.id === toId);
  if (!source || !target) return ["edge: both nodes must exist"];
  const srcSpec = registry.nodes[source.kind];
  const dstSpec = registry.nodes[target.kind];
  if (!srcSpec || !dstSpec) return ["edge: unknown node kind"];
  const out = srcSpec.ports.find((p) => p.name === fromPort && p.direction === "out");
  const inP = dstSpec.ports.find((p) => p.name === toPort && p.direction === "in");
  if (!out) return ["edge: '" + fromPort + "' is not an OUT port of kind '" + source.kind + "'"];
  if (!inP) return ["edge: '" + toPort + "' is not an IN port of kind '" + target.kind + "'"];
  if (!portTypesCompatible(out.type, inP.type)) {
    return [
      "edge: port types do not match ('" + out.type + "' on '" + source.kind + "." + fromPort +
      "' vs '" + inP.type + "' on '" + target.kind + "." + toPort + "')",
    ];
  }
  return [];
}

/** Invalid connects must leave the graph untouched (passes through). */
export function connectReducer(
  registry: RegistrySnapshot,
  graph: Graph,
  c: Connection,
): { graph: Graph; error: string | null } {
  const fromPort = c.sourceHandle;
  const toPort = c.targetHandle;
  if (!c.source || !c.target || !fromPort || !toPort) {
    return { graph, error: "edge: connection needs both handles" };
  }
  const reasons = validateConnect(registry, graph, c.source, c.target, fromPort, toPort);
  if (reasons.length > 0) return { graph, error: reasons[0] };
  const edge: DomainEdge = {
    id: nextEdgeId(graph),
    from: c.source,
    to: c.target,
    fromPort,
    toPort,
  };
  return { graph: { ...graph, edges: [...graph.edges, edge] }, error: null };
}

/** Default props for a freshly added node: the server applies its own
 * defaults (per /api/nodes registry), so an empty {} object - which every
 * kind accepts by /api/validate - is the registry-consistent default. */
export function addNodeReducer(
  registry: RegistrySnapshot,
  graph: Graph,
  kind: string,
  position: DomainPosition,
): { graph: Graph; id: string | null; error: string | null } {
  if (!registry.nodes[kind]) {
    return { graph, id: null, error: "unknown node kind '" + kind + "'" };
  }
  const node: DomainNode = {
    id: nextNodeId(graph, "n"),
    kind,
    props: {},
    position: { x: position.x, y: position.y },
  };
  return { graph: { ...graph, nodes: [...graph.nodes, node] }, id: node.id, error: null };
}

/* ------------------------------------------------------------------ */
/* xyflow <-> domain mapping                                          */
/* ------------------------------------------------------------------ */

export interface PipelineNodeData extends Record<string, unknown> {
  kind: string;
  label?: string;
  props: Record<string, unknown>;
  ports: PortSpec[];
  runState?: "idle" | "running" | "done" | "error";
}

export type PipelineNode = Node<PipelineNodeData, "pipeline">;

export function toXYNodes(
  graph: Graph,
  registry: RegistrySnapshot,
  prev?: PipelineNode[],
): PipelineNode[] {
  const prevById = new Map((prev ?? []).map((n) => [n.id, n]));
  return graph.nodes.map((n) => {
    // Data identity: when the domain node is unchanged (same kind/label
    // props/ports object references) reuse the previous data object so the
    // memoized PipelineNode does not re-render on unrelated updates.
    const p = prevById.get(n.id);
    const ports = registry.nodes[n.kind]?.ports ?? [];
    const stableData =
      p !== undefined &&
      p.data.kind === n.kind &&
      p.data.label === n.label &&
      p.data.props === n.props &&
      p.data.ports === ports;
    const data: PipelineNodeData = stableData
      ? p.data
      : {
          kind: n.kind,
          ...(n.label !== undefined ? { label: n.label } : {}),
          props: n.props,
          ports,
        };
    return {
      id: n.id,
      type: "pipeline" as const,
      position: n.position,
      // Keep measured geometry + interaction flags; the domain node (a
      // flow/0.1 document shape) must not absorb xyflow-only fields.
      width: p?.width,
      height: p?.height,
      dragging: p?.dragging,
      selected: p?.selected,
      data,
    };
  });
}

export function toXYEdges(graph: Graph): Edge[] {
  return graph.edges.map((e) => ({
    id: e.id,
    source: e.from,
    target: e.to,
    sourceHandle: e.fromPort,
    targetHandle: e.toPort,
  }));
}

/** Apply an already-projected set of xyflow nodes back onto the domain
 * graph: positions updated, deleted nodes removed, kind/props/label
 * preserved from the existing domain node. xyflow-only fields
 * (width/height/dragging/selected) intentionally never land on the
 * domain node — they persist on the store projection (see toXYNodes). */
export function fromXYNodes(nodes: Node[], existing: Graph): Graph {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const keep = existing.nodes.filter((n) => byId.has(n.id));
  const changed = keep.map((n) => {
    const xy = byId.get(n.id)!;
    if (xy.position.x === n.position.x && xy.position.y === n.position.y) return n;
    return { ...n, position: { x: xy.position.x, y: xy.position.y } };
  });
  return { nodes: changed, edges: existing.edges };
}

/* ------------------------------------------------------------------ */
/* Store                                                              */
/* ------------------------------------------------------------------ */

export const useFlowStore = create<FlowState>((set, get) => ({
  graph: { nodes: [], edges: [] },
  projection: [],
  selection: null,
  inspectorTab: "properties",
  runStatus: null,
  paletteCollapsed: false,
  inspectorCollapsed: false,
  registry: null,
  registryError: null,
  error: null,

  setGraph: (graph) => set({ graph, projection: [] }),
  setSelection: (selection) => set({ selection }),
  setInspectorTab: (inspectorTab) => set({ inspectorTab }),
  setRunStatus: (runStatus) => set({ runStatus }),
  setPaletteCollapsed: (paletteCollapsed) => set({ paletteCollapsed }),
  setInspectorCollapsed: (inspectorCollapsed) => set({ inspectorCollapsed }),
  setRegistry: (registry) => set({ registry, registryError: null }),
  setRegistryError: (registryError) => set({ registryError }),
  setError: (error) => set({ error }),

  addNode: (kind, position) => {
    const registry = get().registry ?? FALLBACK_REGISTRY;
    const res = addNodeReducer(registry, get().graph, kind, position);
    if (res.error) {
      set({ error: res.error });
      return null;
    }
    set({ graph: res.graph });
    return res.id;
  },

  applyNodesChanges: (changes) => {
    const g = get();
    const xyNodes = applyNodeChanges(
      changes,
      toXYNodes(g.graph, g.registry ?? FALLBACK_REGISTRY, g.projection),
    ) as PipelineNode[];
    const graph = fromXYNodes(xyNodes, g.graph);
    // Mirror select changes into store.selection: the last select change
    // wins (selected:false clears — e.g. the pane click deselection).
    let selection: string | null | undefined;
    for (const c of changes) {
      if (c.type === "select") selection = c.selected ? c.id : null;
    }
    set({
      graph,
      projection: xyNodes,
      ...(selection === undefined ? {} : { selection }),
    });
  },

  applyEdgesChanges: (changes) => {
    // Only "remove" changes can alter the domain graph; every other
    // xyflow edge change kind (select/dimensions/...) is projection-only.
    // Removals are counted per id (NOT a keep-Set, which would collapse
    // duplicate-id edges into one removal) so exactly one domain edge per
    // requested remove disappears (T8 review IMPORTANT-2).
    const removals = new Map<string, number>();
    for (const c of changes) {
      if (c.type === "remove") removals.set(c.id, (removals.get(c.id) ?? 0) + 1);
    }
    if (removals.size === 0) return;
    const graph = get().graph;
    const edges = graph.edges.filter((e) => {
      const pending = removals.get(e.id) ?? 0;
      if (pending <= 0) return true;
      removals.set(e.id, pending - 1);
      return false;
    });
    set({ graph: { ...graph, edges } });
  },

  connect: (c: Connection) => {
    const registry = get().registry ?? FALLBACK_REGISTRY;
    const res = connectReducer(registry, get().graph, c);
    if (res.error) {
      set({ error: res.error });
      return false;
    }
    set({ graph: res.graph });
    return true;
  },
}));
