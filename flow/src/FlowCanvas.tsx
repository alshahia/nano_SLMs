import { useCallback, useEffect, useRef, useState } from "react";
import {
  ReactFlow,
  Background,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import type { Connection, NodeChange } from "@xyflow/react";
import { useFlowStore, toXYNodes, toXYEdges, FALLBACK_REGISTRY } from "./store";
import PipelineNode from "./nodes/PipelineNode";
import { usePaletteKinds } from "./Palette";
import "@xyflow/react/dist/style.css";

const nodeTypes = { pipeline: PipelineNode };

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

/** Canvas: controlled ReactFlow wired into the store (apply nodes/edges
 * changes into store.graph), registry-validated onConnect (refuse +
 * toast), HTML5 drag-from-palette, right-click add menu and Ctrl+K.
 * Both menu paths add at the mouse position. */
function FlowCanvasInner() {
  const graph = useFlowStore((s) => s.graph);
  const error = useFlowStore((s) => s.error);
  const setError = useFlowStore((s) => s.setError);
  const addNode = useFlowStore((s) => s.addNode);
  const connect = useFlowStore((s) => s.connect);
  const applyNodesChanges = useFlowStore((s) => s.applyNodesChanges);
  const registry = useFlowStore((s) => s.registry);

  const { screenToFlowPosition } = useReactFlow();
  const { kinds } = usePaletteKinds();

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
    const rect = document.querySelector(".canvas")?.getBoundingClientRect();
    lastMouseRef.current = { x: clientX - (rect?.left ?? 0), y: clientY - (rect?.top ?? 0) };
  }, []);

  /* Ctrl+K anywhere: open/close the search modal at the mouse position. */
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && (e.key === "k" || e.key === "K")) {
        e.preventDefault();
        setSearchOpen((open) => !open);
        setMenu(null);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const addAtMouse = useCallback(
    (kind: string) => {
      setMenu(null);
      setSearchOpen(false);
      if (kind === "" || kind === "__close__") return;
      const m = lastMouseRef.current;
      const rect = document.querySelector(".canvas")?.getBoundingClientRect();
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
    <main className="canvas">
      <ReactFlow
        nodes={toXYNodes(graph, registry ?? FALLBACK_REGISTRY)}
        edges={toXYEdges(graph)}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onConnect={onConnect}
        onPaneContextMenu={(e) => { e.preventDefault(); setLastMouse(e.clientX, e.clientY); setMenu({ x: e.clientX, y: e.clientY }); }}
        onNodeContextMenu={(e) => { e.preventDefault(); setLastMouse(e.clientX, e.clientY); setMenu({ x: e.clientX, y: e.clientY }); }}
        onPaneClick={() => { setMenu(null); setSearchOpen(false); }}
        onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = "copy"; }}
        onDrop={onDrop}
        onNodeClick={() => setMenu(null)}
      >
        <Background />
      </ReactFlow>

      {menu !== null && (
        <div className="add-menu-wrap" style={{ left: menu.x, top: menu.y }}>
          <AddMenu kinds={kinds} onPick={addAtMouse} onSearch={() => { setMenu(null); setSearchOpen(true); }} />
        </div>
      )}

      {searchOpen && (
        <div
          className="add-menu-wrap"
          style={{ left: lastMouseRef.current.x, top: lastMouseRef.current.y }}
          onClick={(e) => e.stopPropagation()}
        >
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
