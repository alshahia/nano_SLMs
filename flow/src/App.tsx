import { useEffect, useRef, useState } from "react";
import Palette from "./Palette";
import FlowCanvas from "./FlowCanvas";
import Inspector from "./Inspector";
import { useFlowStore, isValidFlowName } from "./store";
import { api, errorMessage } from "./api";
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
    </div>
  );
}

/** Header toolbar. Open = GET /api/flows + picker modal -> GET the picked
 * flow -> store.openFlow (which also resets the xyflow projection via
 * setGraph; an empty projection just means an unmeasured canvas, visually
 * benign). Save = modal name prompt with client-side slug validation ->
 * store.saveFlow (PUT /api/flows/{name}). Errors surface through the
 * existing store.error toast channel (rendered in FlowCanvas). Run /
 * Validate buttons are intentionally NOT wired here (Task 10). */
function Toolbar() {
  const saveFlow = useFlowStore((s) => s.saveFlow);
  const openFlow = useFlowStore((s) => s.openFlow);
  const setError = useFlowStore((s) => s.setError);

  /* File modal mode: null | "open" (flow list picker) | "save" (name
   * prompt). */
  const [modal, setModal] = useState<null | "open" | "save">(null);
  const inputRef = useRef<HTMLInputElement>(null);

  /* Escape closes the active modal (capture phase so it wins over the
   * canvas handlers; closing twice is a no-op). */
  useEffect(() => {
    if (!modal) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        setModal(null);
      }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [modal]);

  useEffect(() => {
    if (modal === "save") inputRef.current?.focus();
  }, [modal]);

  const submitSave = async () => {
    const name = inputRef.current?.value ?? "";
    if (!isValidFlowName(name)) {
      setError(
        "flow name must match [a-z0-9-]{1,64} (lowercase letters, digits, dashes)",
      );
      return;
    }
    const ok = await saveFlow(name);
    if (ok) {
      setModal(null);
      setError(null);
    }
  };

  return (
    <header className="toolbar">
      <span className="toolbar-title">flow</span>
      <button id="toolbar-open" aria-label="Open saved flow" onClick={() => setModal("open")}>
        Open
      </button>
      <button id="toolbar-save" aria-label="Save current flow" onClick={() => setModal("save")}>
        Save
      </button>

      {modal === "open" && (
        <FlowPicker
          onPick={openFlow}
          onDismiss={() => setModal(null)}
        />
      )}

      {modal === "save" && (
        <div className="modal-backdrop" onClick={() => setModal(null)}>
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
              <button onClick={() => setModal(null)}>Cancel</button>
              <button onClick={() => void submitSave()}>Save</button>
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
