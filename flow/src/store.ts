import { create } from "zustand";
import type { Edge, Node, NodeChange, EdgeChange, Connection } from "@xyflow/react";
import { applyNodeChanges } from "@xyflow/react";
import { api, errorMessage, type FlowDocument } from "./api";

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
  /** Backend exit_code (parallel to state done/error; null while running).
   * Shared with the PipelineNode dot tooltip ("exit code N"). */
  exitCode?: number | null;
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
  /** Slug of the graph as saved/opened (null while purely unsaved). Run
   * wiring PUT-saves under this name; Validate uses it for meta.name
   * (choice: an unsaved graph validates as meta.name "untitled" —
   * TOCTOU-free, the server validates the document, not the slug). */
  currentFlowName: string | null;
  /** Graph document the server last accepted via POST /api/validate —
   * the raw material for the read-only Preview summary card. */
  validatedDoc: FlowDocument | null;
  /** Confirmation line from the last successful Stop (STOP flag path). */
  stopInfo: string | null;
  setGraph: (g: Graph) => void;
  setSelection: (id: string | null) => void;
  setInspectorTab: (t: InspectorTab) => void;
  setRunStatus: (s: RunStatus | null) => void;
  setPaletteCollapsed: (c: boolean) => void;
  setInspectorCollapsed: (c: boolean) => void;
  setRegistry: (r: RegistrySnapshot) => void;
  setRegistryError: (e: string | null) => void;
  setError: (e: string | null) => void;
  /** Task 10 wiring: validate the UNSAVED graph (POST /api/validate),
   * arm a run (PUT-save then POST /api/run -> runStatus running + Run log
   * tab), and request the checkpoint-aligned stop (POST /api/run/stop). */
  validateFlow: () => Promise<boolean>;
  runGraph: () => Promise<boolean>;
  stopRun: () => Promise<boolean>;
  /** Task 9 inspector props write-back (see updateNodePropsReducer). */
  updateNodeProps: (id: string, props: Record<string, unknown>) => void;
  /** Task 9 file actions: Open = GET /api/flows/{name} -> setGraph (which
   * also resets the xyflow projection via setGraph); Save = PUT
   * /api/flows/{name}. Both surface errors through the existing
   * store.error toast channel and never leave a half-applied graph.
   * saveFlow keeps the collapsed names awaitable for the toolbar modal. */
  openFlow: (name: string) => Promise<boolean>;
  saveFlow: (name: string) => Promise<boolean>;
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
/* Task 9: props editing + flow name slug helpers                     */
/* ------------------------------------------------------------------ */

/** Editor widget to render for a given registry prop. The train string
 * presets render as selects; numeric_props render as number inputs;
 * anything else is a free-text input. Pure, registry-driven so the
 * per-kind table in the T7 contract is honoured (empty-props kinds lead
 * to the "(no editable properties)" note in the Inspector). */
export type PropWidget = "number" | "select" | "text";

/** The train kind's two string props are preset-name selects. */
const SELECT_PROPS = new Set(["preset", "lr_preset"]);

export function propWidgetType(spec: NodeSpec, prop: string): PropWidget {
  if (SELECT_PROPS.has(prop)) return "select";
  if (spec.numeric_props.includes(prop)) return "number";
  return "text";
}

/** Placeholder select options for the train preset / lr_preset widgets.
 * These names are copied from flow/server/config_gen.py PRESETS /
 * LR_PRESETS (which in turn mirror webui/app.py). The inspector dropdowns
 * are a client-side copy on purpose (MVP); actual value parity is enforced
 * by the backend AST-parity test (T5) — a server-side rename that does not
 * update this list shows up as a T5 failure, not a silent config drift. */
export const TRAIN_PRESET_OPTIONS: string[] = [
  "Small (~12M, smoke)",
  "Medium (~101M, pilot)",
  "Large (~226M, target)",
];
export const LR_PRESET_OPTIONS: string[] = [
  "Pretrain 4e-4",
  "Conservative 2e-4",
  "Fine-tune 3e-5",
];

/** Options for a props select widget (empty -> fall back to free text). */
export function propSelectOptions(
  prop: string,
): string[] | null {
  if (prop === "preset") return TRAIN_PRESET_OPTIONS;
  if (prop === "lr_preset") return LR_PRESET_OPTIONS;
  return null;
}

/** Client-side slug validation for the Save/Open name inputs
 * ([a-z0-9-]{1,64}). The server re-validates authoritatively; this only
 * gives immediate feedback and avoids a doomed request round-trip. */
export const FLOW_SLUG_RE = /^[a-z0-9-]{1,64}$/;

export function isValidFlowName(name: string): boolean {
  return FLOW_SLUG_RE.test(name);
}

/** Toast-friendly truncation of a long validation error list: keep the
 * first 3 lines verbatim and summarize the rest as "+N more" (the toast
 * has a max-width and the backend can emit a line per validator check). */
export function truncateErrorList(errors: string[], keep = 3): string[] {
  if (errors.length <= keep) return errors;
  return [...errors.slice(0, keep), "+" + (errors.length - keep) + " more"];
}

/** Poll interval math for the Run log watcher (carry-over T9 finding (d)):
 * the base cadence is 2 s; after 3 consecutive poll failures stretch to
 * ~30 s so a dead backend does not spam fetch, and the successful read
 * resets the counter (failure count is kept by the watcher loop). */
export const POLL_BASE_MS = 2000;
export const POLL_BACKOFF_MS = 30000;
export const POLL_FAILS_BEFORE_BACKOFF = 3;

export function nextPollDelay(consecutiveFailures: number): number {
  return consecutiveFailures >= POLL_FAILS_BEFORE_BACKOFF
    ? POLL_BACKOFF_MS
    : POLL_BASE_MS;
}

/** Build the flow/0.1 PUT document for the current graph. The document
 * meta name echoes the slug under which the graph is saved server-side. */
export function flowDocument(name: string, graph: Graph): FlowDocument {
  return { schema: "flow/0.1", meta: { name }, graph };
}

/** Pure props write-back: replace node.props in place-by-id and return a
 * NEW graph (validator-agnostic here — the server validates on save and
 * on POST /api/validate). Unknown ids return the original graph object. */
export function updateNodePropsReducer(
  graph: Graph,
  id: string,
  props: Record<string, unknown>,
): Graph {
  if (!graph.nodes.some((n) => n.id === id)) return graph;
  return {
    ...graph,
    nodes: graph.nodes.map((n) => (n.id === id ? { ...n, props } : n)),
  };
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
  /** Backend exit_code, only shown/tooltiped in terminal dot states. */
  exitCode?: number | null;
}

export type PipelineNode = Node<PipelineNodeData, "pipeline">;

/**
 * runState/exitCode threading (Task 10, honest MVP simplification): the
 * backend runs one whole-graph pipeline — nodes are NOT individually
 * resolved. So while runStatus.state === "running" EVERY node's dot
 * shows "running"; at a terminal done/error the dots flip set-wide and
 * the title tooltip carries the backend exit_code. Per-node phases are
 * a future engine feature; until then this is deliberately global, not
 * faked per node.
 */
export function toXYNodes(
  graph: Graph,
  registry: RegistrySnapshot,
  prev?: PipelineNode[],
  runState: "idle" | "running" | "done" | "error" = "idle",
  exitCode: number | null = null,
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
      p.data.ports === ports &&
      p.data.runState === runState &&
      (p.data.exitCode ?? null) === exitCode;
    const data: PipelineNodeData = stableData
      ? p.data
      : {
          kind: n.kind,
          ...(n.label !== undefined ? { label: n.label } : {}),
          props: n.props,
          ports,
          runState,
          exitCode,
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
  currentFlowName: null,
  validatedDoc: null,
  stopInfo: null,

  setGraph: (graph) => set({ graph, projection: [], validatedDoc: null }),
  updateNodeProps: (id, props) => {
    const g = get();
    const next = updateNodePropsReducer(g.graph, id, props);
    // Unknown id keeps the same graph object -> no state churn.
    // Any real graph edit invalidates the cached validatedDoc so the
    // Preview card can never claim freshness over a stale document
    // (T10 review IMPORTANT-2).
    if (next !== g.graph) set({ graph: next, validatedDoc: null });
  },
  openFlow: async (name) => {
    try {
      const doc = await api.getFlow(name);
      set({ graph: doc.graph, projection: [], error: null, currentFlowName: name, validatedDoc: null });
      return true;
    } catch (e) {
      set({ error: errorMessage(e) });
      return false;
    }
  },
  saveFlow: async (name) => {
    if (!isValidFlowName(name)) {
      set({
        error: "flow name must match [a-z0-9-]{1,64} (lowercase letters, digits, dashes)",
      });
      return false;
    }
    try {
      await api.saveFlow(name, flowDocument(name, get().graph));
      set({ error: null, currentFlowName: name });
      return true;
    } catch (e) {
      set({ error: errorMessage(e) });
      return false;
    }
  },
  // Task 10 run wiring -------------------------------------------------
  // Validate ALWAYS posts the unsaved graph: the doc meta.name is the
  // saved slug when there is one, else the literal "untitled" (documented
  // choice above). A successful response caches validatedDoc for the
  // Preview summary; errors go to the toast, first 3 + "+N more".
  validateFlow: async () => {
    const name = get().currentFlowName;
    const doc = flowDocument(
      name !== null && isValidFlowName(name) ? name : "untitled",
      get().graph,
    );
    try {
      const r = await api.validateFlow(doc);
      if (r.ok) {
        // Distinct success marker on the toast channel ("OK:" prefix) so
        // a passing validate is VISIBLE, not a silent null (T10 review
        // MISSING-1). The prefix distinguishes it from error toasts.
        set({ validatedDoc: doc, error: "OK: validation passed — document accepted" });
        return true;
      }
      set({ validatedDoc: null, error: truncateErrorList(r.errors).join(" · ") });
      return false;
    } catch (e) {
      set({ validatedDoc: null, error: errorMessage(e) });
      return false;
    }
  },
  // Run = PUT-save the current graph under its slug, then POST /api/run.
  // 400 preflight errors[] and 409 busy detail land in the toast channel
  // verbatim (formatApiError already prefers the errors/detail shapes);
  // on success runStatus arms the Run log watcher (which start polls).
  runGraph: async () => {
    const name = get().currentFlowName;
    if (name === null || !isValidFlowName(name)) {
      set({ error: "Run needs a saved flow: use Save first (name must match [a-z0-9-]{1,64})" });
      return false;
    }
    try {
      await api.saveFlow(name, flowDocument(name, get().graph));
    } catch (e) {
      set({ error: errorMessage(e) });
      return false;
    }
    try {
      const r = await api.runFlow(name);
      set({
        runStatus: { state: "running", message: "started pid " + String(r.pid), exitCode: undefined },
        stopInfo: null,
        inspectorTab: "run-log",
        error: null,
      });
      return true;
    } catch (e) {
      set({ error: errorMessage(e) });
      return false;
    }
  },
  // Stop is the ONLY run control by design (NO kill button): it writes
  // the U11 STOP flag; the trainer exits cleanly at the next checkpoint
  // save. A 409 ("no live GPU job") surface through the toast verbatim.
  stopRun: async () => {
    try {
      const r = await api.runStop();
      set({ error: null, stopInfo: "stop flag written: " + r.stop_flag });
      return true;
    } catch (e) {
      set({ error: errorMessage(e) });
      return false;
    }
  },
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
    set({ graph: res.graph, validatedDoc: null });
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
    // Carry-over T9 finding (b): a remove change that deletes the node the
    // Inspector is currently editing must clear the stale selection, or the
    // Properties panel would keep rendering a ghost node's props.
    if (selection === undefined && get().selection !== null) {
      const alive = new Set(graph.nodes.map((n) => n.id));
      if (!alive.has(get().selection as string)) selection = null;
    }
    set({
      graph,
      projection: xyNodes,
      validatedDoc: null,
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
    set({ graph: { ...graph, edges }, validatedDoc: null });
  },

  connect: (c: Connection) => {
    const registry = get().registry ?? FALLBACK_REGISTRY;
    const res = connectReducer(registry, get().graph, c);
    if (res.error) {
      set({ error: res.error });
      return false;
    }
    set({ graph: res.graph, validatedDoc: null });
    return true;
  },
}));
