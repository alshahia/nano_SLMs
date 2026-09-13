import { useCallback, useEffect, useRef, useState } from "react";
import {
  ReactFlow,
  Background,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import type { Connection, EdgeChange, NodeChange } from "@xyflow/react";
import { useFlowStore, toXYNodes, toXYEdges, FALLBACK_REGISTRY } from "./store";
import PipelineNode from "./nodes/PipelineNode";
import { usePaletteKinds } from "./Palette";
import "@xyflow/react/dist/style.css";

const nodeTypes = { pipeline: PipelineNode };

/* Approximate viewport footprint used to clamp the context-menu open
 * position (the add-menu is ~170px min-width plus the search row, up to
 * seven rows tall; 200x260 covers it with headroom). */
const MENU_W = 200;
const MENU_H = 260;

/** Add-node menu opened by right-click anywhere on the canvas (MVP
 * required UX) with one entry per registry kind plus "search… (Ctrl+K)".
 * Adds happen at the mouse position (flow coordinates). */
function AddMenu({
  kinds,
  onPick,
  onSearch,
}: {
  kinds: string[];
  onPick: (kind: string) => void;
  onSearch: () => void;
}) {
  return (
    <div className="add-menu" role="menu">
      {kinds.map((kind) => (
        <button key={kind} role="menuitem" onClick={() => onPick(kind)}>
          {kind}
        </button>
      ))}
      <button role="menuitem" onClick={onSearch} className="add-menu-search">
        search… (Ctrl+K)
      </button>
    </div>
  );
}

/** Ctrl+K search modal: filter box, arrow-key navigation, Enter adds the
 * selected kind at the mouse position; Escape closes, selection no-op. */
function SearchModal({
  kinds,
  onPick,
  open,
}: {
  kinds: string[];
  onPick: (kind: string) => void;
  open: boolean;
}) {
  const [query, setQuery] = useState("");
  const [index, setIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setQuery("");
      setIndex(0);
      inputRef.current?.focus();
    }
  }, [open]);

  if (!open) return null;
  const filtered = kinds.filter((k) => k.includes(query.toLowerCase()));
  return (
    <div className="search-backdrop" onClick={() => onPick("__close__")}>
      <div
        className="search-modal"
        role="dialog"
        aria-label="Add node search"
        onClick={(e) => e.stopPropagation()}
      >
        <input
          ref={inputRef}
          value={query}
          placeholder="search kinds…"
          onChange={(e) => {
            setQuery(e.target.value);
            setIndex(0);
          }}
          onKeyDown={(e) => {
            if (e.key === "Escape") onPick("__close__");
            else if (e.key === "ArrowDown") setIndex((i) => Math.min(i + 1, filtered.length - 1));
            else if (e.key === "ArrowUp") setIndex((i) => Math.max(i - 1, 0));
            else if (e.key === "Enter") {
              if (filtered.length > 0 && filtered[index]) onPick(filtered[index]);
            }
          }}
        />
        <ul className="search-list">
          {filtered.map((k, i) => (
            <li key={k}>
              <button
                className={i === index ? "active" : ""}
                onMouseEnter={() => setIndex(i)}
                onClick={() => onPick(k)}
              >
                {k}
              </button>
            </li>
          ))}
          {filtered.length === 0 && <li className="search-empty">no match</li>}
        </ul>
      </div>
    </div>
  );
}

/** Canvas: controlled ReactFlow wired into the store (apply node AND edge
 * changes into store.graph — edge deletion included), registry-validated
 * onConnect (refuse + toast), HTML5 drag-from-palette, right-click add
 * menu and Ctrl+K. Both menu paths add at the mouse position. */
function FlowCanvasInner() {
  const graph = useFlowStore((s) => s.graph);
  const error = useFlowStore((s) => s.error);
  const setError = useFlowStore((s) => s.setError);
  const addNode = useFlowStore((s) => s.addNode);
  const connect = useFlowStore((s) => s.connect);
  const applyNodesChanges = useFlowStore((s) => s.applyNodesChanges);
  const applyEdgesChanges = useFlowStore((s) => s.applyEdgesChanges);
  const registry = useFlowStore((s) => s.registry);
  const projection = useFlowStore((s) => s.projection);

  const { screenToFlowPosition } = useReactFlow();
  const { kinds } = usePaletteKinds();

  /* Canvas ref replaces the old document.querySelector(".canvas") global
   * lookup (T8 review MINOR-7); refs for the menu/modal outside-close. */
  const canvasRef = useRef<HTMLElement | null>(null);
  const menuWrapRef = useRef<HTMLDivElement | null>(null);
  const searchWrapRef = useRef<HTMLDivElement | null>(null);
  const [menu, setMenu] = useState<{ x: number; y: number } | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const lastMouseRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  /* Toast clears itself a moment after appearing (canvas owns the timer). */
  useEffect(() => {
    if (!error) return;
    const t = window.setTimeout(() => setError(null), 4000);
    return () => window.clearTimeout(t);
  }, [error, setError]);

  const setLastMouse = useCallback((clientX: number, clientY: number) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    lastMouseRef.current = { x: clientX - (rect?.left ?? 0), y: clientY - (rect?.top ?? 0) };
  }, []);

  /* Ctrl+K toggles the search modal anywhere; Escape closes the menu and
   * modal at document level (also when focus is outside the input). The
   * modal's own Escape handler runs alongside — closing twice is a no-op. */
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && (e.key === "k" || e.key === "K")) {
        e.preventDefault();
        setSearchOpen((open) => !open);
        setMenu(null);
      } else if (e.key === "Escape") {
        setMenu(null);
        setSearchOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  /* Close the menu/modal on any pointer-down outside of them. The palette
   * and inspector areas live outside the canvas, so this covers them; the
   * pane/node click handlers keep closing on canvas clicks as before. */
  useEffect(() => {
    if (!menu && !searchOpen) return;
    const onDocPointerDown = (e: MouseEvent) => {
      const target = e.target as Node;
      if (menuWrapRef.current?.contains(target) || searchWrapRef.current?.contains(target)) return;
      setMenu(null);
      setSearchOpen(false);
    };
    document.addEventListener("mousedown", onDocPointerDown);
    return () => document.removeEventListener("mousedown", onDocPointerDown);
  }, [menu, searchOpen]);

  /* Context-menu open position, clamped inside the window so it cannot
   * clip at the right/bottom canvas/viewport edges (T8 review MINOR-5). */
  const openMenuAt = useCallback(
    (clientX: number, clientY: number) => {
      setLastMouse(clientX, clientY);
      setMenu({
        x: Math.max(0, Math.min(clientX, window.innerWidth - MENU_W)),
        y: Math.max(0, Math.min(clientY, window.innerHeight - MENU_H)),
      });
    },
    [setLastMouse],
  );

  const addAtMouse = useCallback(
    (kind: string) => {
      setMenu(null);
      setSearchOpen(false);
      if (kind === "" || kind === "__close__") return;
      const m = lastMouseRef.current;
      const rect = canvasRef.current?.getBoundingClientRect();
      const pos = screenToFlowPosition({
        x: (rect?.left ?? 0) + m.x,
        y: (rect?.top ?? 0) + m.y,
      });
      addNode(kind, pos);
    },
    [addNode, screenToFlowPosition],
  );

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => applyNodesChanges(changes),
    [applyNodesChanges],
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      // Edge deletions must round-trip into store.graph (T8 review
      // IMPORTANT-2); non-removal changes are projection-only there.
      applyEdgesChanges(changes);
    },
    [applyEdgesChanges],
  );

  const onConnect = useCallback(
    (c: Connection) => {
      // Registry-validated in the reducer; on reject nothing in the graph
      // changes and store.error drives the toast below.
      connect(c);
    },
    [connect],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const kind = e.dataTransfer.getData("application/flow-node-kind");
      if (!kind) return;
      addNode(kind, screenToFlowPosition({ x: e.clientX, y: e.clientY }));
    },
    [addNode, screenToFlowPosition],
  );

  return (
    <main ref={canvasRef} className="canvas">
      <ReactFlow
        nodes={toXYNodes(graph, registry ?? FALLBACK_REGISTRY, projection)}
        edges={toXYEdges(graph)}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onPaneContextMenu={(e) => { e.preventDefault(); openMenuAt(e.clientX, e.clientY); }}
        onNodeContextMenu={(e) => { e.preventDefault(); openMenuAt(e.clientX, e.clientY); }}
        onPaneClick={() => { setMenu(null); setSearchOpen(false); }}
        onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = "copy"; }}
        onDrop={onDrop}
        onNodeClick={() => setMenu(null)}
      >
        <Background />
      </ReactFlow>

      {menu !== null && (
        <div className="add-menu-wrap" style={{ left: menu.x, top: menu.y }} ref={menuWrapRef}>
          <AddMenu kinds={kinds} onPick={addAtMouse} onSearch={() => { setMenu(null); setSearchOpen(true); }} />
        </div>
      )}

      {searchOpen && (
        /* Rendered directly under the canvas (no positioning wrapper):
         * .search-modal is position:fixed (App.css), so absolutely
         * offsetting a wrapper at lastMouseRef was dead positioning — the
         * centered dialog placement lives entirely in the modal CSS. */
        <div ref={searchWrapRef}>
          <SearchModal open kinds={kinds} onPick={addAtMouse} />
        </div>
      )}

      {error !== null && (
        <div className="toast" role="alert">
          {error}
        </div>
      )}
    </main>
  );
}

export default function FlowCanvas() {
  return (
    <ReactFlowProvider>
      <FlowCanvasInner />
    </ReactFlowProvider>
  );
}
