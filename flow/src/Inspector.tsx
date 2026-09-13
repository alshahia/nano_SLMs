import { useFlowStore, type InspectorTab } from "./store";

const TABS: { id: InspectorTab; label: string }[] = [
  { id: "properties", label: "Properties" },
  { id: "run-log", label: "Run Log" },
  { id: "preview", label: "Preview" },
];

export default function Inspector() {
  const tab = useFlowStore((s) => s.inspectorTab);
  const setTab = useFlowStore((s) => s.setInspectorTab);
  const collapsed = useFlowStore((s) => s.inspectorCollapsed);
  const setCollapsed = useFlowStore((s) => s.setInspectorCollapsed);

  if (collapsed) {
    return (
      <aside className="inspector inspector-collapsed">
        <button onClick={() => setCollapsed(false)}>«</button>
      </aside>
    );
  }

  return (
    <aside className="inspector">
      <button onClick={() => setCollapsed(true)}>»</button>
      <div className="inspector-tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
          >
              {t.label}
          </button>
        ))}
      </div>
      <div className="inspector-panel" role="tabpanel">
        <p>{TABS.find((t) => t.id === tab)?.label} panel</p>
      </div>
    </aside>
  );
}
