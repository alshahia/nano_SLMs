import Palette from "./Palette";
import FlowCanvas from "./FlowCanvas";
import Inspector from "./Inspector";
import "./App.css";

export default function App() {
  return (
    <div className="shell">
      <Palette />
      <FlowCanvas />
      <Inspector />
    </div>
  );
}
