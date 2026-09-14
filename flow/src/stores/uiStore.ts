import type { FlowState } from "../store";

/** Toast-friendly truncation of a long validation error list: keep the
 * first 3 lines verbatim and summarize the rest as "+N more" (the toast
 * has a max-width and the backend can emit a line per validator check). */
export function truncateErrorList(errors: string[], keep = 3): string[] {
  if (errors.length <= keep) return errors;
  return [...errors.slice(0, keep), "+" + (errors.length - keep) + " more"];
}

export type InspectorTab = "properties" | "run-log" | "preview";

/* ------------------------------------------------------------------ */
/* UI slice state                                                      */
/* ------------------------------------------------------------------ */

import type { StoreApi } from "zustand";
type SetFlow = StoreApi<FlowState>["setState"];
type GetFlow = StoreApi<FlowState>["getState"];

export interface UiState {
  selection: string | null;
  inspectorTab: InspectorTab;
  paletteCollapsed: boolean;
  inspectorCollapsed: boolean;
  /** User-visible error / toast line; reducers never mutate graph on reject. */
  error: string | null;
  /** Task 11 infer-handoff dialog state. */
  inferHandoffNodeId: string | null;
  setSelection: (id: string | null) => void;
  setInspectorTab: (t: InspectorTab) => void;
  setPaletteCollapsed: (c: boolean) => void;
  setInspectorCollapsed: (c: boolean) => void;
  setError: (e: string | null) => void;
  /** Task 11 infer-handoff dialog slice (pure, reducer-safe; see
   * src/inferHandoff.ts for the rendered content). */
  openInferHandoff: (nodeId: string) => void;
  dismissInferHandoff: () => void;
}

/** UI slice of the composed flow store: selection, inspector tabs,
 * collapse flags, toast channel, dialog state. */
export function createUiSlice(set: SetFlow, _get?: GetFlow): UiState {
  return {
    selection: null,
    inspectorTab: "properties",
    paletteCollapsed: false,
    inspectorCollapsed: false,
    error: null,
    inferHandoffNodeId: null,

    setSelection: (selection) => set({ selection }),
    setInspectorTab: (inspectorTab) => set({ inspectorTab }),
    setPaletteCollapsed: (paletteCollapsed) => set({ paletteCollapsed }),
    setInspectorCollapsed: (inspectorCollapsed) => set({ inspectorCollapsed }),
    setError: (error) => set({ error }),
    openInferHandoff: (nodeId) => set({ inferHandoffNodeId: nodeId }),
    dismissInferHandoff: () => set({ inferHandoffNodeId: null }),
  };
}
