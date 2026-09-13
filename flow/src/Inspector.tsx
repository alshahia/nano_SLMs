import { useEffect, useRef, useState } from "react";
import {
  useFlowStore,
  FALLBACK_REGISTRY,
  propWidgetType,
  propSelectOptions,
  updateNodePropsReducer,
  type InspectorTab,
  type NodeSpec,
  type PropWidget,
} from "./store";
import { api, errorMessage, mapRunStatus } from "./api";

const TABS: { id: InspectorTab; label: string }[] = [
  { id: "properties", label: "Properties" },
  { id: "run-log", label: "Run Log" },
  { id: "preview", label: "Preview" },
];

/** One labeled editor row for a registry prop. Widget selection comes
 * from propWidgetType (registry-driven); number inputs coerce on change. */
function PropRow({
  name,
  value,
  widget,
  onChange,
}: {
  name: string;
  value: unknown;
  widget: PropWidget;
  onChange: (v: unknown) => void;
}) {
  const options = widget === "select" ? propSelectOptions(name) : null;
  const inputId = "prop-" + name;
  return (
    <div className="prop-row">
      <label htmlFor={inputId}>{name}</label>
      {widget === "select" && options !== null ? (
        <select
          id={inputId}
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value)}
        >
          {!options.includes(String(value)) && <option value="">(unset)</option>}
          {options.map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      ) : widget === "number" ? (
        <input
          id={inputId}
          type="number"
          value={typeof value === "number" && Number.isFinite(value) ? String(value) : ""}
          onChange={(e) => {
            if (e.target.value === "") onChange(undefined);
            else onChange(Number(e.target.value));
          }}
        />
      ) : (
        <input
          id={inputId}
          type="text"
          value={value === undefined || value === null ? "" : String(value)}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </div>
  );
}

/** Advanced disclosure: raw props JSON editor. Honesty label is explicit
 * (DESIGN advanced YAML/Knobs section): what you type is the node's props
 * object verbatim — no validation happens here; the server re-checks
 * everything on POST /api/validate and on PUT /api/flows/{name}. */
function AdvancedPropsEditor({ nodeId, propsJson }: { nodeId: string; propsJson: string }) {
  const updateNodeProps = useFlowStore((s) => s.updateNodeProps);
  const setError = useFlowStore((s) => s.setError);
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(propsJson);
  // Reset the draft when the selected node (or its props) change.
  useEffect(() => setDraft(propsJson), [nodeId, propsJson]);

  return (
    <details className="advanced-props" onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}>
      <summary>Advanced: raw props JSON</summary>
      {open && (
        <>
          <p className="honesty-label">
            honest: this is YAML-adjacent — the JSON below becomes the node's
            props verbatim; nothing is validated here, the server does that
            on save/validate.
          </p>
          <textarea
            aria-label={"raw props JSON for node " + nodeId}
            value={draft}
            rows={6}
            onChange={(e) => setDraft(e.target.value)}
          />
          <button
            onClick={() => {
              try {
                const parsed: unknown = JSON.parse(draft);
                if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
                  setError("advanced props: JSON must be an object (props are key → value)");
                  return;
                }
                updateNodeProps(nodeId, parsed as Record<string, unknown>);
                setError(null);
              } catch {
                setError("advanced props: not valid JSON");
              }
            }}
          >
            Apply to node
          </button>
        </>
      )}
    </details>
  );
}

/** Properties tab for store.selection: widgets per the registry snapshot
 * (never the kind guess), "(no editable properties)" for the empty-props
 * kinds (dataset / eval / infer per the T7 contract table). */
function PropertiesPanel() {
  const selection = useFlowStore((s) => s.selection);
  const graph = useFlowStore((s) => s.graph);
  const registry = useFlowStore((s) => s.registry);
  const setError = useFlowStore((s) => s.setError);
  const updateNodeProps = useFlowStore((s) => s.updateNodeProps);

  const node = selection === null ? null : graph.nodes.find((n) => n.id === selection);
  if (!node) return <p className="inspector-empty">select a node on the canvas</p>;
  const spec: NodeSpec | undefined =
    (registry ?? FALLBACK_REGISTRY).nodes[node.kind];

  if (!spec || spec.props.length === 0) {
    return (
      <>
        <p className="inspector-empty">(no editable properties)</p>
        {spec && spec.props.length === 0 && (
          /** Advanced JSON editing still makes sense for raw round-trip
           * fidelity (e.g. an old document's extra keys) even when the
           * registry lists no widgets for the kind. */
          <AdvancedPropsEditor nodeId={node.id} propsJson={JSON.stringify(node.props, null, 2)} />
        )}
      </>
    );
  }

  const setProp = (name: string, value: unknown) => {
    const next = { ...node.props };
    if (value === undefined) delete next[name];
    else next[name] = value;
    // Server validates on save/validate; the client write path keeps the
    // reducer pure (updateNodePropsReducer) and optimism is honest here.
    updateNodeProps(node.id, next);
  };

  return (
    <>
      <p className="prop-kind">kind: {node.kind}</p>
      {spec.props.map((p) => (
        <PropRow
          key={p}
          name={p}
          value={node.props[p]}
          widget={propWidgetType(spec, p)}
          onChange={(v) => {
            setError(null);
            setProp(p, v);
          }}
        />
      ))}
      <AdvancedPropsEditor nodeId={node.id} propsJson={JSON.stringify(node.props, null, 2)} />
    </>
  );
}

/** Run log tab: polls GET /api/run/status every 2 s while a run is being
 * watched (store.runStatus is set), streams the tail into a scrollable
 * pre with bottom auto-adherence (sticks unless the user scrolled up) and
 * a "no live run" empty state otherwise. */
function RunLogPanel() {
  const runStatus = useFlowStore((s) => s.runStatus);
  const setRunStatus = useFlowStore((s) => s.setRunStatus);
  const [tail, setTail] = useState<string[]>([]);
  const [pollError, setPollError] = useState<string | null>(null);
  const preRef = useRef<HTMLPreElement | null>(null);
  // Stick-to-bottom heuristic: true until the user scrolls up away from
  // the bottom edge; every successful tail read re-evaluates adherence.
  const atBottomRef = useRef(true);

  /* Poll only while a run is being watched AND still live; a terminal
   * mapped state (done/error) settles the panel and stops the interval
   * (the toolbar Run button re-arms via setRunStatus in Task 10). */
  const watching = runStatus !== null && runStatus.state === "running";

  useEffect(() => {
    if (!watching) return;
    let cancelled = false;
    const poll = () => {
      api
        .runStatus()
        .then((s) => {
          if (cancelled) return;
          setPollError(null);
          const next = mapRunStatus(s);
          setRunStatus(next);
          if (s.tail.length > 0) setTail(s.tail);
          if (atBottomRef.current && preRef.current) {
            preRef.current.scrollTop = preRef.current.scrollHeight;
          }
          // Once the mapped state is terminal the watcher can stop (a
          // fresh run re-arms polling via setRunStatus from the toolbar).
        })
        .catch((e) => {
          if (cancelled) return;
          setPollError(errorMessage(e));
        });
    };
    poll();
    const t = window.setInterval(poll, 2000);
    return () => {
      cancelled = true;
      window.clearInterval(t);
    };
  }, [watching, setRunStatus]);

  useEffect(() => {
    if (atBottomRef.current && preRef.current) {
      preRef.current.scrollTop = preRef.current.scrollHeight;
    }
  }, [tail]);

  if (runStatus === null || runStatus.state === "idle") {
    return <p className="inspector-empty">no live run</p>;
  }

  return (
    <div className="run-log">
      <p className={runStatus.state === "error" ? "run-state run-state-error" : "run-state"} role="status">
        {runStatus.state}
        {runStatus.message ? " — " + runStatus.message : ""}
      </p>
      {pollError !== null && <p className="honesty-label">{pollError}</p>}
      <pre
        ref={preRef}
        className="run-tail"
        aria-label="live run output tail"
        onScroll={(e) => {
          const el = e.currentTarget;
          atBottomRef.current = el.scrollTop + el.clientHeight >= el.scrollHeight - 4;
        }}
      >
        {tail.length === 0 ? "(no output yet)" : tail.join("\n")}
      </pre>
    </div>
  );
}

export default function Inspector() {
  const tab = useFlowStore((s) => s.inspectorTab);
  const setTab = useFlowStore((s) => s.setInspectorTab);
  const collapsed = useFlowStore((s) => s.inspectorCollapsed);
  const setCollapsed = useFlowStore((s) => s.setInspectorCollapsed);

  if (collapsed) {
    return (
      <aside className="inspector inspector-collapsed">
        <button onClick={() => setCollapsed(false)} aria-label="Expand inspector">
          «
        </button>
      </aside>
    );
  }

  return (
    <aside className="inspector">
      <button onClick={() => setCollapsed(true)} aria-label="Collapse inspector">
        »
      </button>
      <div className="inspector-tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            id={"inspector-tab-" + t.id}
            aria-selected={tab === t.id}
            aria-controls={"inspector-panel-" + t.id}
            onClick={() => setTab(t.id)}
          >
              {t.label}
          </button>
        ))}
      </div>
      {/* One panel element per known tab (hidden ones inert) so each tab
       * button's aria-controls target actually exists. */}
      {TABS.map((t) => (
        <div
          key={t.id}
          id={"inspector-panel-" + t.id}
          role="tabpanel"
          className="inspector-panel"
          hidden={tab !== t.id}
          aria-labelledby={"inspector-tab-" + t.id}
        >
          {tab !== t.id ? null : t.id === "properties" ? (
            <PropertiesPanel />
          ) : t.id === "run-log" ? (
            <RunLogPanel />
          ) : (
            <p className="inspector-empty">config preview lands after validate/run wiring</p>
          )}
        </div>
      ))}
    </aside>
  );
}
