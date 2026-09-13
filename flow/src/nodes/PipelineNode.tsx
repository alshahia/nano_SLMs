import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { PipelineNodeData, PipelineNode } from "../store";

import "./PipelineNode.css";

/** xyflow node renderer: title, prop badges, run-state dot, and one
 * Handle per registered port (direction -> Handle type). Port metadata
 * comes from the registry snapshot cached in the store (via /api/nodes). */
function PipelineNode({ data, selected }: NodeProps<PipelineNode>) {
  const ports = data.ports ?? [];
  const propEntries = Object.entries(data.props ?? {});
  return (
    <div className={"pipeline-node" + (selected ? " selected" : "")}>
      <div className="pipeline-node-head">
        {/* TODO(Tasks 9/10): placeholder only — wire real run state from
            POST /api/run + GET /api/run/status into node.data.runState when
            run wiring lands; do not fake a wire before that. */}
        <span className={"run-dot run-dot-" + (data.runState ?? "idle")} title={"run state: " + (data.runState ?? "idle")} />
        <span className="pipeline-node-title">{data.label ?? data.kind}</span>
      </div>
      {propEntries.length > 0 && (
        <div className="pipeline-node-props">
          {propEntries.map(([k, v]) => (
            <span key={k} className="prop-badge">
              {k}={String(v)}
            </span>
          ))}
        </div>
      )}
      <div className="pipeline-node-ports">
        {ports.map((p) => {
          const isIn = p.direction === "in";
          const label = p.name;
          return (
            <div key={p.name} className={"pipeline-port pipeline-port-" + p.direction}>
              {isIn ? <span className="pipeline-port-label">{label}</span> : null}
              <Handle id={p.name} type={isIn ? "target" : "source"} position={isIn ? Position.Left : Position.Right} isConnectable={true} />
              {!isIn ? <span className="pipeline-port-label">{label}</span> : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default memo(PipelineNode);
