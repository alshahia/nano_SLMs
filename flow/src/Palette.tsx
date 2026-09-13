import { useFlowStore } from "./store";

const NODE_KINDS = ["dataset", "tokenize", "train", "eval", "merge", "export"];

export default function Palette() {
  const collapsed = useFlowStore((s) => s.paletteCollapsed);
  const setCollapsed = useFlowStore((s) => s.setPaletteCollapsed);

  return (
    <aside className="palette">
      <button onClick={() => setCollapsed(!collapsed)}>
        {collapsed ? "»" : "«"}
      </button>
      {collapsed ? null : (
        <div className="palette-cards">
          {NODE_KINDS.map((kind) => (
            <div key={kind} className="palette-card">
              {kind}
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}
