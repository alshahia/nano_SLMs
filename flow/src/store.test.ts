import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import type { RegistrySnapshot } from "./store";
import type { NodeChange } from "@xyflow/react";
import { api, formatApiError, mapRunStatus, errorMessage } from "./api";
import type { ApiRunStatus } from "./api";
import type { Graph } from "./store";
import {
  useFlowStore,
  addNodeReducer,
  connectReducer,
  nextNodeId,
  nextEdgeId,
  portTypesCompatible,
  toXYNodes,
  toXYEdges,
  fromXYNodes,
  validateConnect,
  propWidgetType,
  propSelectOptions,
  isValidFlowName,
  updateNodePropsReducer,
  flowDocument,
} from "./store";

const REGISTRY: RegistrySnapshot = {
  valid_kinds: ["dataset", "prepare", "tokenize", "train", "eval", "infer"],
  nodes: {
    dataset: {
      ports: [
        { name: "cleaned", direction: "out", type: "raw-dir: dataset name/rows", "burst-format": "row-batch" },
      ],
      props: [],
      numeric_props: [],
      gate: null,
    },
    prepare: {
      ports: [
        { name: "raw-dir", direction: "in", type: "raw-dir", "burst-format": "file-list" },
        { name: "cleaned-dir", direction: "out", type: "cleaned-dir", "burst-format": "file-list" },
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
describe("flow store (T1 shell state)", () => {
  beforeEach(() => {
    useFlowStore.setState({
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
    });
  });

  it("has the initial P1 shell state", () => {
    const s = useFlowStore.getState();
    expect(s.graph).toEqual({ nodes: [], edges: [] });
    expect(s.selection).toBeNull();
    expect(s.inspectorTab).toBe("properties");
    expect(s.runStatus).toBeNull();
  });

  it("setters update their slices", () => {
    const s = useFlowStore.getState();
    s.setInspectorTab("run-log");
    expect(useFlowStore.getState().inspectorTab).toBe("run-log");
    s.setPaletteCollapsed(true);
    expect(useFlowStore.getState().paletteCollapsed).toBe(true);
    s.setInspectorCollapsed(true);
    expect(useFlowStore.getState().inspectorCollapsed).toBe(true);
  });
});

describe("addNode reducer", () => {
  it("adds nodes with unique deterministic ids n1, n2 ...", () => {
    useFlowStore.getState().setRegistry(REGISTRY);
    const id1 = useFlowStore.getState().addNode("dataset", { x: 10, y: 20 });
    const id2 = useFlowStore.getState().addNode("prepare", { x: 220, y: 20 });
    expect(id1).toBe("n1");
    expect(id2).toBe("n2");
    const g = useFlowStore.getState().graph;
    expect(g.nodes.map((n) => [n.id, n.kind])).toEqual([
      ["n1", "dataset"],
      ["n2", "prepare"],
    ]);
    expect(g.nodes[0].position).toEqual({ x: 10, y: 20 });
  });

  it("default props come from the registry (empty prop objects)", () => {
    const res = addNodeReducer(REGISTRY, { nodes: [], edges: [] }, "prepare", { x: 0, y: 0 });
    expect(res.id).toBe("n1");
    expect(res.graph.nodes[0].props).toEqual({});
    const dataset = addNodeReducer(REGISTRY, { nodes: [], edges: [] }, "dataset", { x: 0, y: 0 });
    expect(dataset.graph.nodes[0].props).toEqual({});
  });

  it("refuses unknown kinds without touching the graph or ids", () => {
    const base = useFlowStore.getState().graph;
    const res = addNodeReducer(REGISTRY, base, "warp", { x: 0, y: 0 });
    expect(res.id).toBeNull();
    expect(res.error).toContain("unknown node kind 'warp'");
    expect(res.graph).toBe(base);
  });

  it("nK ids skip over existing ids", () => {
    expect(nextNodeId({ nodes: [{ id: "n3", kind: "eval", props: {}, position: { x: 0, y: 0 } }], edges: [] })).toBe("n4");
    expect(nextNodeId({ nodes: [], edges: [] })).toBe("n1");
  });
});
describe("connect reducer (registry-validated edges)", () => {
  const graph = {
    nodes: [
      { id: "n1", kind: "dataset", props: {}, position: { x: 0, y: 0 } },
      { id: "n2", kind: "prepare", props: {}, position: { x: 100, y: 0 } },
      { id: "n3", kind: "tokenize", props: {}, position: { x: 200, y: 0 } },
      { id: "n4", kind: "train", props: {}, position: { x: 300, y: 0 } },
    ],
    edges: [],
  };

  it("accepts dataset -> prepare and records fromPort/toPort", () => {
    const res = connectReducer(REGISTRY, graph, {
      source: "n1", target: "n2", sourceHandle: "cleaned", targetHandle: "raw-dir",
    });
    expect(res.error).toBeNull();
    expect(res.graph.edges[0]).toEqual({ id: "e1", from: "n1", to: "n2", fromPort: "cleaned", toPort: "raw-dir" });
  });

  it("refuses IN->IN and unknown-orientation connects", () => {
    const inToIn = connectReducer(REGISTRY, graph, {
      source: "n2", target: "n2", sourceHandle: "raw-dir", targetHandle: "raw-dir",
    });
    expect(inToIn.error).toContain("is not an OUT port of kind 'prepare'");
    expect(inToIn.graph).toBe(graph);
    const badTarget = connectReducer(REGISTRY, graph, {
      source: "n1", target: "n2", sourceHandle: "cleaned", targetHandle: "cleaned-dir",
    });
    expect(badTarget.error).toContain("is not an IN port of kind 'prepare'");
    expect(badTarget.graph).toBe(graph);
  });

  it("refuses mismatched port types with a reason string", () => {
    const reasons = validateConnect(REGISTRY, graph, "n1", "n3", "cleaned", "shard-dir");
    expect(reasons.length).toBe(1);
    expect(portTypesCompatible("raw-dir", "raw-dir: dataset name/rows")).toBe(true);
    expect(portTypesCompatible("raw-dir", "cleaned-dir")).toBe(false);
    expect(portTypesCompatible("shard-dir", "ckpt-dir")).toBe(false);
  });

  it("refuses connects that reference missing nodes", () => {
    const res = connectReducer(REGISTRY, graph, {
      source: "nX", target: "n2", sourceHandle: "x", targetHandle: "raw-dir",
    });
    expect(res.error).toContain("nodes must exist");
  });
});

describe("controlled onNodesChange applies into store.graph", () => {
  beforeEach(() => {
    useFlowStore.setState({
      graph: {
        nodes: [
          { id: "n1", kind: "dataset", props: {}, position: { x: 0, y: 0 } },
          { id: "n2", kind: "prepare", props: { rows: 10 }, position: { x: 5, y: 6 } },
        ],
        edges: [{ id: "e1", from: "n1", to: "n2", fromPort: "cleaned", toPort: "raw-dir" }],
      },
      registry: REGISTRY,
      projection: [],
      selection: null,
      inspectorTab: "properties",
      runStatus: null,
      paletteCollapsed: false,
      inspectorCollapsed: false,
      registryError: null,
      error: null,
    });
  });

  it("applies a position change and keeps edges intact", () => {
    const changes: NodeChange[] = [
      { id: "n1", type: "position", position: { x: 42, y: 7 } },
    ];
    useFlowStore.getState().applyNodesChanges(changes);
    const g = useFlowStore.getState().graph;
    expect(g.nodes[0].position).toEqual({ x: 42, y: 7 });
    expect(g.nodes[1].position).toEqual({ x: 5, y: 6 });
    expect(g.edges).toEqual([{ id: "e1", from: "n1", to: "n2", fromPort: "cleaned", toPort: "raw-dir" }]);
  });

  it("applies a remove change and drops the node from the graph", () => {
    const changes: NodeChange[] = [{ id: "n2", type: "remove" }];
    useFlowStore.getState().applyNodesChanges(changes);
    const g = useFlowStore.getState().graph;
    expect(g.nodes.map((n) => n.id)).toEqual(["n1"]);
  });

  it("round-trips through the xyflow projection", () => {
    const g = useFlowStore.getState().graph;
    const xyNodes = toXYNodes(g, REGISTRY);
    expect(xyNodes[1].data.kind).toBe("prepare");
    expect(xyNodes[1].data.props).toEqual({ rows: 10 });
    expect(xyNodes[1].data.ports).toEqual(REGISTRY.nodes.prepare.ports);
    expect(toXYEdges(g)).toEqual([
      { id: "e1", source: "n1", target: "n2", sourceHandle: "cleaned", targetHandle: "raw-dir" },
    ]);
    const back = fromXYNodes(
      xyNodes.map((n) => ({ ...n, position: { x: n.position.x + 1, y: n.position.y } })),
      g,
    );
    expect(back.nodes[0].position).toEqual({ x: 1, y: 0 });
    expect(back.nodes[1].props).toEqual({ rows: 10 });
  });
});

describe("connect action on the store (refuse leaves graph intact)", () => {
  beforeEach(() => {
    useFlowStore.setState({
      graph: {
        nodes: [
          { id: "n1", kind: "dataset", props: {}, position: { x: 0, y: 0 } },
          { id: "n2", kind: "prepare", props: {}, position: { x: 100, y: 0 } },
        ],
        edges: [],
      },
      registry: REGISTRY,
      projection: [],
      selection: null,
      inspectorTab: "properties",
      runStatus: null,
      paletteCollapsed: false,
      inspectorCollapsed: false,
      registryError: null,
      error: null,
    });
  });

  it("valid connect succeeds; invalid connect refuses graph and sets toast", () => {
    const s = useFlowStore.getState();
    expect(s.connect({ source: "n1", target: "n2", sourceHandle: "cleaned", targetHandle: "raw-dir" })).toBe(true);
    const afterValid = useFlowStore.getState().graph;
    expect(afterValid.edges).toHaveLength(1);
    const connect2 = useFlowStore.getState().connect;
    expect(connect2({ source: "n2", target: "n2", sourceHandle: "raw-dir", targetHandle: "raw-dir" })).toBe(false);
    const st = useFlowStore.getState();
    expect(st.error).toContain("is not an OUT port of kind 'prepare'");
    expect(st.graph).toEqual(afterValid);
    st.setError(null);
    expect(useFlowStore.getState().error).toBeNull();
  });
});

describe("registry fetch (mocked fetch, no server)", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("api.getNodes parses the /api/nodes snapshot", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(REGISTRY), { status: 200 })),
    );
    const snap = await api.getNodes();
    expect(snap.valid_kinds).toEqual(["dataset", "prepare", "tokenize", "train", "eval", "infer"]);
    expect(snap.nodes.dataset.ports[0].name).toBe("cleaned");
    expect(snap.gates.train).toBe("gpu");
  });

  it("formatApiError maps both backend error shapes", () => {
    expect(formatApiError(400, "Bad Request", "/api/flows/x", { errors: ["a", "b"] })).toBe("a; b");
    expect(formatApiError(404, "Not Found", "/api/flows/x", { detail: "flow x not found" })).toBe("flow x not found");
    expect(formatApiError(500, "Oops", "/x", null)).toBe("500 Oops: /x");
  });
});

describe("edge ids (nextEdgeId, T8 fix: no more duplicate e1)", () => {
  const graph = {
    nodes: [
      { id: "n1", kind: "dataset", props: {}, position: { x: 0, y: 0 } },
      { id: "n2", kind: "prepare", props: {}, position: { x: 100, y: 0 } },
      { id: "n3", kind: "tokenize", props: {}, position: { x: 200, y: 0 } },
    ],
    edges: [],
  };

  it("nextEdgeId mirrors nextNodeId semantics over graph.edges", () => {
    expect(nextEdgeId({ nodes: [], edges: [] })).toBe("e1");
    expect(
      nextEdgeId({
        nodes: [],
        edges: [
          { id: "e3", from: "n1", to: "n2", fromPort: "a", toPort: "b" },
          { id: "e7", from: "n2", to: "n3", fromPort: "a", toPort: "b" },
        ],
      }),
    ).toBe("e8");
  });

  it("two consecutive edge creations get distinct ids", () => {
    const one = connectReducer(REGISTRY, graph, {
      source: "n1", target: "n2", sourceHandle: "cleaned", targetHandle: "raw-dir",
    });
    expect(one.error).toBeNull();
    expect(one.graph.edges[0].id).toBe("e1");
    const two = connectReducer(REGISTRY, one.graph, {
      source: "n2", target: "n3", sourceHandle: "cleaned-dir", targetHandle: "cleaned-dir",
    });
    expect(two.error).toBeNull();
    expect(two.graph.edges[1].id).toBe("e2");
    expect(new Set(two.graph.edges.map((e) => e.id)).size).toBe(2);
  });

  it("invalid-connect refusal leaves the graph and the next edge id stable", () => {
    const refused = connectReducer(REGISTRY, graph, {
      source: "n2", target: "n2", sourceHandle: "raw-dir", targetHandle: "raw-dir",
    });
    expect(refused.graph).toBe(graph);
    expect(refused.error).toContain("is not an OUT port of kind 'prepare'");
    const after = connectReducer(REGISTRY, refused.graph, {
      source: "n1", target: "n2", sourceHandle: "cleaned", targetHandle: "raw-dir",
    });
    expect(after.error).toBeNull();
    expect(after.graph.edges.map((e) => e.id)).toEqual(["e1"]);
  });
});

describe("applyEdgesChanges (edge deletion wired, duplicate-id guard)", () => {
  beforeEach(() => {
    useFlowStore.setState({
      graph: {
        nodes: [
          { id: "n1", kind: "dataset", props: {}, position: { x: 0, y: 0 } },
          { id: "n2", kind: "prepare", props: {}, position: { x: 1, y: 1 } },
        ],
        edges: [
          { id: "e1", from: "n1", to: "n2", fromPort: "cleaned", toPort: "raw-dir" },
          { id: "e2", from: "n1", to: "n2", fromPort: "cleaned", toPort: "raw-dir" },
          { id: "e3", from: "n1", to: "n2", fromPort: "cleaned", toPort: "raw-dir" },
        ],
      },
      registry: REGISTRY,
      projection: [],
      selection: null,
      inspectorTab: "properties",
      runStatus: null,
      paletteCollapsed: false,
      inspectorCollapsed: false,
      registryError: null,
      error: null,
    });
  });

  it("removes exactly the requested edge and keeps the rest", () => {
    useFlowStore.getState().applyEdgesChanges([{ id: "e2", type: "remove" }]);
    expect(useFlowStore.getState().graph.edges.map((e) => e.id)).toEqual(["e1", "e3"]);
  });

  it("one remove request cannot collapse two same-id edges", () => {
    useFlowStore.setState({
      graph: {
        nodes: [
          { id: "n1", kind: "dataset", props: {}, position: { x: 0, y: 0 } },
          { id: "n2", kind: "prepare", props: {}, position: { x: 1, y: 1 } },
        ],
        edges: [
          { id: "e1", from: "n1", to: "n2", fromPort: "cleaned", toPort: "raw-dir" },
          { id: "e1", from: "n1", to: "n2", fromPort: "cleaned", toPort: "raw-dir" },
          { id: "e2", from: "n1", to: "n2", fromPort: "cleaned", toPort: "raw-dir" },
        ],
      },
    });
    // The old keep-Set implementation removed BOTH "e1" edges here.
    useFlowStore.getState().applyEdgesChanges([{ id: "e1", type: "remove" }]);
    expect(useFlowStore.getState().graph.edges.map((e) => e.id)).toEqual(["e1", "e2"]);
  });

  it("non-removal change kinds leave the domain graph untouched", () => {
    const before = useFlowStore.getState().graph;
    useFlowStore.getState().applyEdgesChanges([{ id: "e2", type: "select", selected: true }]);
    expect(useFlowStore.getState().graph).toBe(before);
  });
});

describe("projection merge (dragging/selected persistence, data identity)", () => {
  beforeEach(() => {
    useFlowStore.setState({
      graph: {
        nodes: [
          { id: "n1", kind: "dataset", props: {}, position: { x: 0, y: 0 } },
          { id: "n2", kind: "prepare", props: { rows: 2 }, position: { x: 5, y: 6 } },
        ],
        edges: [],
      },
      registry: REGISTRY,
      projection: [],
      selection: null,
      inspectorTab: "properties",
      runStatus: null,
      paletteCollapsed: false,
      inspectorCollapsed: false,
      registryError: null,
      error: null,
    });
  });

  it("dragging survives the project -> applyNodeChanges -> project round-trip", () => {
    useFlowStore.getState().applyNodesChanges([
      { id: "n1", type: "position", position: { x: 42, y: 9 }, dragging: true },
    ]);
    const st = useFlowStore.getState();
    expect(st.graph.nodes[0].position).toEqual({ x: 42, y: 9 });
    const nextProjection = toXYNodes(st.graph, REGISTRY, st.projection);
    expect(nextProjection[0].dragging).toBe(true);
    expect(nextProjection[0].position).toEqual({ x: 42, y: 9 });
  });

  it("select changes update store.selection and the projection selected flag", () => {
    useFlowStore.getState().applyNodesChanges([{ id: "n2", type: "select", selected: true }]);
    const st = useFlowStore.getState();
    expect(st.selection).toBe("n2");
    expect(toXYNodes(st.graph, REGISTRY, st.projection)[1].selected).toBe(true);
    useFlowStore.getState().applyNodesChanges([{ id: "n2", type: "select", selected: false }]);
    expect(useFlowStore.getState().selection).toBeNull();
  });

  it("unchanged domain nodes keep their previous data object identity", () => {
    const baseline = toXYNodes(useFlowStore.getState().graph, REGISTRY);
    useFlowStore.setState({ projection: baseline });
    useFlowStore.getState().applyNodesChanges([
      { id: "n1", type: "position", position: { x: 9, y: 9 } },
    ]);
    const proj = useFlowStore.getState().projection;
    expect(proj[0].data).toBe(baseline[0].data);
    expect(useFlowStore.getState().graph.nodes[0].position).toEqual({ x: 9, y: 9 });
  });
});

/* ------------------------------------------------------------------ */
/* Task 9: inspector widgets, run status mapping, file actions         */
/* ------------------------------------------------------------------ */

describe("props widget mapping per kind (T7 contract table)", () => {
  it("numeric registry props render as number inputs", () => {
    expect(propWidgetType(REGISTRY.nodes.prepare, "rows")).toBe("number");
    expect(propWidgetType(REGISTRY.nodes.prepare, "min_chars")).toBe("number");
    expect(propWidgetType(REGISTRY.nodes.tokenize, "seq_len")).toBe("number");
    expect(propWidgetType(REGISTRY.nodes.train, "steps")).toBe("number");
  });

  it("train preset / lr_preset render as selects (server-parity lists)", () => {
    expect(propWidgetType(REGISTRY.nodes.train, "preset")).toBe("select");
    expect(propWidgetType(REGISTRY.nodes.train, "lr_preset")).toBe("select");
    expect(propSelectOptions("preset")).not.toBeNull();
    expect(propSelectOptions("lr_preset")).not.toBeNull();
    // The placeholder copies are non-empty and align with
    // flow/server/config_gen.py PRESETS / LR_PRESETS names.
    expect((propSelectOptions("preset") ?? []).length).toBeGreaterThan(0);
    expect((propSelectOptions("lr_preset") ?? []).length).toBeGreaterThan(0);
  });

  it("unknown string props fall back to free text", () => {
    expect(propWidgetType({ ports: [], props: ["x"], numeric_props: [], gate: null }, "x")).toBe("text");
  });

  it("empty-props kinds (dataset/eval/infer) have no widgets at all", () => {
    for (const kind of ["dataset", "eval", "infer"] as const) {
      expect(REGISTRY.nodes[kind].props).toEqual([]);
    }
  });
});

describe("flow name slug validation (client-side honesty check)", () => {
  it("accepts valid slugs only", () => {
    expect(isValidFlowName("alpha-run")).toBe(true);
    expect(isValidFlowName("0123456789012345678901234567890123456789012345678901234567890123")).toBe(true); // 64
    expect(isValidFlowName("")).toBe(false);
    expect(isValidFlowName("Alpha")).toBe(false);
    expect(isValidFlowName("has space")).toBe(false);
    expect(isValidFlowName("01234567890123456789012345678901234567890123456789012345678901234")).toBe(false); // 65
  });
});

describe("props write-back (validator-agnostic, pure reducer)", () => {
  const graph: Graph = {
    nodes: [
      { id: "n1", kind: "train", props: { preset: "Small (~12M, smoke)" }, position: { x: 0, y: 0 } },
    ],
    edges: [],
  };

  it("updateNodePropsReducer replaces props by id and keeps others", () => {
    const res = updateNodePropsReducer(graph, "n1", { steps: 4, preset: "Large (~226M, target)" });
    expect(res).not.toBe(graph);
    expect(res.nodes[0].props).toEqual({ steps: 4, preset: "Large (~226M, target)" });
    expect(res.nodes[0].kind).toBe("train");
    expect(graph.nodes[0].props).toEqual({ preset: "Small (~12M, smoke)" }); // untouched
  });

  it("updateNodePropsReducer returns the same graph for an unknown id (no churn)", () => {
    expect(updateNodePropsReducer(graph, "nZ", { x: 1 })).toBe(graph);
  });

  it("store action writes props back into the selected node only", () => {
    useFlowStore.setState({
      graph: {
        nodes: [
          { id: "n1", kind: "train", props: {}, position: { x: 0, y: 0 } },
          { id: "n2", kind: "prepare", props: {}, position: { x: 1, y: 1 } },
        ],
        edges: [],
      },
      registry: REGISTRY,
      projection: [],
      selection: null,
      inspectorTab: "properties",
      runStatus: null,
      paletteCollapsed: false,
      inspectorCollapsed: false,
      registryError: null,
      error: null,
    });
    useFlowStore.getState().updateNodeProps("n2", { rows: 100 });
    const g = useFlowStore.getState().graph;
    expect(g.nodes[0].props).toEqual({});
    expect(g.nodes[1].props).toEqual({ rows: 100 });
    // Unknown id is a silent no-op, not a crash.
    useFlowStore.getState().updateNodeProps("nZZ", {});
    expect(useFlowStore.getState().graph).toBe(g);
  });

  it("flowDocument wraps the graph into the flow/0.1 PUT shape", () => {
    const doc = flowDocument("alpha-run", graph);
    expect(doc).toEqual({
      schema: "flow/0.1",
      meta: { name: "alpha-run" },
      graph,
    });
  });
});

describe("ApiRunStatus -> RunStatus mapping", () => {
  const status = (partial: Partial<ApiRunStatus>): ApiRunStatus => ({
    running: false,
    exit_code: null,
    started_at: null,
    exit_at: null,
    tail: [],
    ...partial,
  });

  it("running=true maps to running regardless of exit_code leftovers", () => {
    expect(mapRunStatus(status({ running: true }))).toEqual({
      state: "running",
      message: "running…",
    });
  });

  it("exit_code 0 maps to done", () => {
    expect(mapRunStatus(status({ running: false, exit_code: 0, exit_at: "now" }))).toEqual({
      state: "done",
      message: "exit code 0 — done",
    });
  });

  it("non-zero exit_code maps to error", () => {
    expect(mapRunStatus(status({ running: false, exit_code: 1 }))).toEqual({
      state: "error",
      message: "exit code 1 — error",
    });
  });

  it("not-running without exit_code maps to idle (no live run)", () => {
    expect(mapRunStatus(status({}))).toEqual({ state: "idle", message: "no live run" });
  });
});

describe("file open/save store actions (mocked fetch)", () => {
  const DOC = {
    schema: "flow/0.1" as const,
    meta: { name: "alpha-run" },
    graph: {
      nodes: [{ id: "n1", kind: "dataset", props: {}, position: { x: 1, y: 2 } }],
      edges: [],
    },
  };

  beforeEach(() => {
    useFlowStore.setState({
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
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("openFlow success GETs the document, replaces the graph and resets the projection", async () => {
    useFlowStore.setState({ projection: [] });
    const fetchMock = vi.fn(async (path: string) => {
      expect(path).toBe("/api/flows/alpha-run");
      return new Response(JSON.stringify(DOC), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);
    await useFlowStore.getState().openFlow("alpha-run");
    expect(useFlowStore.getState().graph).toEqual(DOC.graph);
    expect(useFlowStore.getState().projection).toEqual([]);
    expect(useFlowStore.getState().error).toBeNull();
  });

  it("openFlow 404 detail failure leaves the graph intact and toasts", async () => {
    const before = useFlowStore.getState().graph;
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            detail: 'flow \'alpha-run\' not found (looked for x)',
          }),
          { status: 404, statusText: "Not Found" },
        ),
      ),
    );
    const ok = await useFlowStore.getState().openFlow("alpha-run");
    expect(ok).toBe(false);
    const st = useFlowStore.getState();
    expect(st.graph).toEqual(before);
    expect(st.error).toBe("flow 'alpha-run' not found (looked for x)");
  });

  it("saveFlow success PUTs the current graph under the given name", async () => {
    useFlowStore.setState({
      graph: {
        nodes: [{ id: "n1", kind: "dataset", props: {}, position: { x: 0, y: 0 } }],
        edges: [],
      },
    });
    const fetchMock = vi.fn(async (path: string, init?: RequestInit) => {
      expect(path).toBe("/api/flows/my-run");
      expect(init?.method).toBe("PUT");
      const body = JSON.parse(String(init?.body)) as {
        meta: { name: string };
        schema: string;
        graph: Graph;
      };
      expect(body.schema).toBe("flow/0.1");
      expect(body.meta).toEqual({ name: "my-run" });
      expect(body.graph).toEqual(useFlowStore.getState().graph);
      return new Response(JSON.stringify({ ok: true, name: "my-run" }), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const ok = await useFlowStore.getState().saveFlow("my-run");
    expect(ok).toBe(true);
    expect(useFlowStore.getState().error).toBeNull();
  });

  it("saveFlow 400 errors[] toast keeps the client graph for another try", async () => {
    useFlowStore.setState({
      graph: {
        nodes: [{ id: "n1", kind: "train", props: { preset: "warp" }, position: { x: 0, y: 0 } }],
        edges: [],
      },
    });
    const before = useFlowStore.getState().graph;
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({ errors: ["train.preset: unknown preset 'warp'"] }),
          { status: 400, statusText: "Bad Request" },
        ),
      ),
    );
    const ok = await useFlowStore.getState().saveFlow("my-run");
    expect(ok).toBe(false);
    const st = useFlowStore.getState();
    expect(st.error).toBe("train.preset: unknown preset 'warp'");
    expect(st.graph).toEqual(before);
  });

  it("saveFlow refuses non-slug names without a doomed request", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const ok = await useFlowStore.getState().saveFlow("Bad Name");
    expect(ok).toBe(false);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(useFlowStore.getState().error).toContain("[a-z0-9-]{1,64}");
  });

  it("network failure during open lands in the toast channel", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("fetch failed");
      }),
    );
    const ok = await useFlowStore.getState().openFlow("alpha-run");
    expect(ok).toBe(false);
    expect(useFlowStore.getState().error).toBe("fetch failed");
  });

  it("errorMessage stringifies non-Error throws", () => {
    expect(errorMessage("boom")).toBe("boom");
  });
});

