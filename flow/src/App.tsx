import { useEffect, useRef, useState } from "react";
import Palette from "./Palette";
import FlowCanvas from "./FlowCanvas";
import Inspector from "./Inspector";
import { useFlowStore, isValidFlowName } from "./store";
import { api, errorMessage } from "./api";
import InferHandoffDialog from "./InferHandoffDialog";
import "./App.css";

/* Throttle window: a focus event refetches the registry at most once per
 * this window (the mount fetch itself counts as an attempt). */
const REGISTRY_REFETCH_THROTTLE_MS = 5000;

/** Cache the /api/nodes registry snapshot in the store on mount; on
 * failure record the error so Palette falls back to its static copy.
 * A refetch is also attempted whenever the window regains focus (at most
 * once per throttle window) so a late-starting backend heals without a
 * manual reload (T8 review MINOR-9). */
export default function App() {
  const setRegistry = useFlowStore((s) => s.setRegistry);
  const setRegistryError = useFlowStore((s) => s.setRegistryError);

  useEffect(() => {
    let cancelled = false;
    let lastAttempt = Date.now();
    const refetch = () => {
      if (cancelled) return;
      api
        .getNodes()
        .then((r) => {
          if (!cancelled) setRegistry(r);
        })
        .catch((e) => {
          if (!cancelled) setRegistryError(errorMessage(e));
        });
    };
    refetch();
    const onFocus = () => {
      if (Date.now() - lastAttempt >= REGISTRY_REFETCH_THROTTLE_MS) {
        lastAttempt = Date.now();
        refetch();
      }
    };
    window.addEventListener("focus", onFocus);
    return () => {
      cancelled = true;
      window.removeEventListener("focus", onFocus);
    };
  }, [setRegistry, setRegistryError]);

  return (
    <div className="app-root">
      <Toolbar />
      <div className="shell">
        <Palette />
        <FlowCanvas />
        <Inspector />
      </div>
      <InferHandoffDialog />
    </div>
  );
}

/** Header toolbar. Open = GET /api/flows + picker modal -> GET the picked
 * flow -> store.openFlow (which also resets the xyflow projection via
 * setGraph; an empty projection just means an unmeasured canvas, visually
 * benign). Save = modal name prompt with client-side slug validation ->
 * store.saveFlow (PUT /api/flows/{name}). Errors surface through the
 * existing store.error toast channel (rendered in FlowCanvas). Both are
 * wired (Task 10): Validate toasts an "OK:" success marker; Run is
 * disabled while a run is live and routes an unsaved graph through the
 * Save modal first. */
function Toolbar() {
  const saveFlow = useFlowStore((s) => s.saveFlow);
  const openFlow = useFlowStore((s) => s.openFlow);
  const setError = useFlowStore((s) => s.setError);
  const validateFlow = useFlowStore((s) => s.validateFlow);
  const runGraph = useFlowStore((s) => s.runGraph);
  const currentFlowName = useFlowStore((s) => s.currentFlowName);
  const runStatus = useFlowStore((s) => s.runStatus);

  /* File modal mode: null | "open" (flow list picker) | "save" (name
   * prompt). */
  const [modal, setModal] = useState<null | "open" | "save">(null);
  /* In-flight guard for the Save modal (carry-over T9 finding (a)): the
   * submit button (and the Enter shortcut) are inert while the PUT is
   * awaiting, so a double-Enter cannot fire two saves. */
  const [saving, setSaving] = useState(false);
  /* One-shot flag so a Run click on an unsaved graph opens the Save modal
   * and continues with runGraph() after that save succeeds. */
  const runAfterSaveRef = useRef(false);
  const inputRef = useRef<HTMLInputElement>(null);

  /* Centralized Save-modal dismissal (T10 review CRITICAL-1): EVERY
   * non-submit dismiss path - backdrop click, Escape, Cancel - must clear
   * the one-shot runAfterSave flag along with closing the modal. A
   * backdrop-dismissed Run prompt that left the flag armed would make a
   * later ordinary Save silently launch an unintended GPU job. Opening
   * the modal WITHOUT the run intent (plain Save button) resets it too.
   * The flag lives in a ref, so this chokepoint is not reachable through
   * reducer-level store tests; covered by this single-path wiring plus
   * this comment (noted in the task report). */
  const dismissSave = () => {
    runAfterSaveRef.current = false;
    setModal(null);
  };

  /* Escape closes the active modal (capture phase so it wins over the
   * canvas handlers; closing twice is a no-op). */
  useEffect(() => {
    if (!modal) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        dismissSave();
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [modal]);

  useEffect(() => {
    if (modal === "save") inputRef.current?.focus();
  }, [modal]);

  const submitSave = async () => {
    if (saving) return; // in-flight guard (T9 fix a)
    const name = inputRef.current?.value ?? "";
    if (!isValidFlowName(name)) {
      setError(
        "flow name must match [a-z0-9-]{1,64} (lowercase letters, digits, dashes)",
      );
      return;
    }
    setSaving(true);
    try {
      const ok = await saveFlow(name);
      if (ok) {
        setModal(null);
        setError(null);
        if (runAfterSaveRef.current) {
          runAfterSaveRef.current = false;
          await runGraph();
        }
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <header className="toolbar">
      <span className="toolbar-title">flow</span>
      <button id="toolbar-open" aria-label="Open saved flow" onClick={() => setModal("open")}>
        Open
      </button>
      {/* Plain Save opens the modal WITHOUT the run intent; reset the
          one-shot flag here so a prior dismissed Run prompt cannot leak
          its armed state into an ordinary save (CRITICAL-1). */}
      <button
        id="toolbar-save"
        aria-label="Save current flow"
        onClick={() => {
          runAfterSaveRef.current = false;
          setModal("save");
        }}
      >
        Save
      </button>
      {/* Task 10 wiring: Validate POSTs the UNSAVED graph document
        * (meta.name = saved slug or "untitled") and toasts ok / first-3
        * errors + "+N more"; Run PUT-saves the graph under its slug and
        * POSTs /api/run, switching to the Run log tab. An unsaved graph
        * routes Run through the Save modal first (one-shot flag). */}
      <button id="toolbar-validate" aria-label="Validate current graph" onClick={() => void validateFlow()}>
        Validate
      </button>
      {/* Running guard (T10 review MINOR-3): Run is inert while a job
          is live, matching Stop's running-only affordance. */}
      <button
        id="toolbar-run"
        aria-label="Run current flow"
        disabled={runStatus?.state === "running"}
        onClick={() => {
          if (currentFlowName !== null && isValidFlowName(currentFlowName)) void runGraph();
          else {
            runAfterSaveRef.current = true;
            setModal("save");
          }
        }}
      >
        Run
      </button>

      {modal === "open" && (
        <FlowPicker
          /* A pick must ALSO dismiss the modal: openFlow alone left the Open
           * dialog covering the canvas after loading (browser drill finding). */
          onPick={(name) => { setModal(null); void openFlow(name); }}
          onDismiss={() => setModal(null)}
        />
      )}

      {modal === "save" && (
        <div className="modal-backdrop" onClick={dismissSave}>
          <div
            className="modal"
            role="dialog"
            aria-label="Save flow"
            onClick={(e) => e.stopPropagation()}
          >
            <label htmlFor="save-name">flow name</label>
            <input
              ref={inputRef}
              id="save-name"
              placeholder="my-run"
              onKeyDown={(e) => {
                if (e.key === "Enter") void submitSave();
              }}
            />
            <div className="modal-actions">
              <button onClick={dismissSave}>Cancel</button>
              <button disabled={saving} onClick={() => void submitSave()}>
                {modal === "save" && saving ? "saving…" : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

/** Body for the Open modal: names come straight from GET /api/flows;
 * the list fetch failure is shown inline and API failures from the
 * subsequent GET/PUT land in the store.error toast. */
function FlowPicker({
  onPick,
  onDismiss,
}: {
  onPick: (name: string) => void;
  onDismiss: () => void;
}) {
  const [names, setNames] = useState<string[] | null>(null);
  const [listError, setListError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getFlows()
      .then((n) => {
        if (!cancelled) setNames(n);
      })
      .catch((e) => {
        if (!cancelled) setListError(errorMessage(e));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="modal-backdrop" onClick={onDismiss}>
      <div
        className="modal"
        role="dialog"
        aria-label="Open flow"
        onClick={(e) => e.stopPropagation()}
      >
        <p className="modal-title">saved flows</p>
        {listError !== null && <p className="honesty-label">{listError}</p>}
        {names === null && <p className="modal-note">loading…</p>}
        {names !== null && names.length === 0 && (
          <p className="modal-note">no saved flows yet</p>
        )}
        <ul className="modal-list">
          {(names ?? []).map((n) => (
            <li key={n}>
              <button onClick={() => onPick(n)}>{n}</button>
            </li>
          ))}
        </ul>
        <div className="modal-actions">
          <button onClick={onDismiss}>Cancel</button>
        </div>
      </div>
    </div>
  );
}
