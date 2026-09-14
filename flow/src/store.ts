/**
 * Behavior-preserving shim (Task 1 of docs/plans/2026-09-13-model-architecture-editor-plan.md).
 *
 * The former 685-line god-store was split into composable zustand slice
 * modules under ./stores:
 *   - graphStore    : domain graph types, pure reducers, xyflow mappers,
 *                     graph document + persistence actions
 *   - registryStore : registry snapshot state + prop-widget helpers
 *                     (+ re-exports of ./nodes/registry for compat)
 *   - uiStore       : InspectorTab, selection, toast channel, dialog state
 *   - runStore      : RunStatus, run/stop wiring, poll-backoff math
 *
 * Every previously exported name is re-exported unchanged and every test
 * consumer (useFlowStore.getState/setState) keeps its exact API, so a
 * single composed store is used: the four slices are created from their
 * slice modules and merged into one useFlowStore instance. Consumers are
 * untouched.
 */
import { create } from "zustand";
import { createRegistrySlice, type RegistryState } from "./stores/registryStore";
import { createUiSlice, type UiState } from "./stores/uiStore";
import { createRunSlice, type RunState } from "./stores/runStore";
import { createGraphSlice, type GraphState } from "./stores/graphStore";

export * from "./stores/graphStore";
export * from "./stores/registryStore";
export * from "./stores/uiStore";
export * from "./stores/runStore";

/** Combined state shape: all four slices, exactly the old FlowState. */
export interface FlowState extends GraphState, RegistryState, UiState, RunState {}

export const useFlowStore = create<FlowState>()((set, get) => ({
  ...createRegistrySlice(set, get),
  ...createUiSlice(set, get),
  ...createRunSlice(set, get),
  ...createGraphSlice(set, get),
}));
