import { ReactFlow, Background } from "@xyflow/react";
import { useFlowStore } from "./store";
import "@xyflow/react/dist/style.css";

export default function FlowCanvas() {
  const graph = useFlowStore((s) => s.graph);
  const onNodesChange = (changes: unknown[]) => {
    void changes;
  };

  return (
    <main className="canvas">
      <ReactFlow nodes={graph.nodes} edges={graph.edges} onNodesChange={onNodesChange}>
        <Background />
      </ReactFlow>
    </main>
  );
}
