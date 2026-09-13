import { create } from "zustand";
import type { Node, Edge } from "@xyflow/react";

export interface Graph {
  nodes: Node[];
  edges: Edge[];
}

export type InspectorTab = "properties" | "run-log" | "preview";

export interface RunStatus {
  state: "idle" | "running" | "done" | "error";
  message?: string;
}

export interface FlowState {
  graph: Graph;
  selection: Node | null;
  inspectorTab: InspectorTab;
  runStatus: RunStatus | null;
  paletteCollapsed: boolean;
  inspectorCollapsed: boolean;
  setGraph: (graph: Graph) => void;
  setSelection: (selection: Node | null) => void;
  setInspectorTab: (tab: InspectorTab) => void;
  setRunStatus: (status: RunStatus | null) => void;
  setPaletteCollapsed: (collapsed: boolean) => void;
  setInspectorCollapsed: (collapsed: boolean) => void;
}

export const useFlowStore = create<FlowState>((set) => ({
  graph: { nodes: [], edges: [] },
  selection: null,
  inspectorTab: "properties",
  runStatus: null,
  paletteCollapsed: false,
  inspectorCollapsed: false,
  setGraph: (graph) => set({ graph }),
  setSelection: (selection) => set({ selection }),
  setInspectorTab: (inspectorTab) => set({ inspectorTab }),
  setRunStatus: (runStatus) => set({ runStatus }),
  setPaletteCollapsed: (paletteCollapsed) => set({ paletteCollapsed }),
  setInspectorCollapsed: (inspectorCollapsed) => set({ inspectorCollapsed }),
}));
