import { useEffect } from "react";
import Palette from "./Palette";
import FlowCanvas from "./FlowCanvas";
import Inspector from "./Inspector";
import { useFlowStore } from "./store";
import { api, errorMessage } from "./api";
import "./App.css";

/** Cache the /api/nodes registry snapshot in the store on mount; on
 * failure record the error so Palette falls back to its static copy. */
export default function App() {
  const setRegistry = useFlowStore((s) => s.setRegistry);
  const setRegistryError = useFlowStore((s) => s.setRegistryError);

  useEffect(() => {
    let cancelled = false;
    api
      .getNodes()
      .then((r) => {
        if (!cancelled) setRegistry(r);
      })
      .catch((e) => {
        if (!cancelled) setRegistryError(errorMessage(e));
      });
    return () => {
      cancelled = true;
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
