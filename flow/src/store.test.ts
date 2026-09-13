import { describe, it, expect, beforeEach } from "vitest";
import { useFlowStore } from "./store";

describe("flow store", () => {
  beforeEach(() => {
    useFlowStore.setState({
      graph: { nodes: [], edges: [] },
      selection: null,
      inspectorTab: "properties",
      runStatus: null,
      paletteCollapsed: false,
      inspectorCollapsed: false,
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
