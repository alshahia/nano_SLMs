import { useEffect } from "react";
import Palette from "./Palette";
import FlowCanvas from "./FlowCanvas";
import Inspector from "./Inspector";
import { useFlowStore } from "./store";
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
    <div className="shell">
      <Palette />
      <FlowCanvas />
      <Inspector />
    </div>
  );
}
