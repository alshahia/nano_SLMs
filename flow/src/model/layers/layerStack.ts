import type { LayerSpec, PropSpec, TensorPort } from "./shared";
import { numProp, requireIn } from "./shared";

const X: TensorPort = { name: "x", label: "Hidden" };
import { pNorms } from "../paramMath";

// layer-level dims propagate to nothing here (inner body graphs carry them);
// they exist so a stack node alone can still report norm params for its depth.
const DEPTH: PropSpec = { name: "depth", kind: "int", default: 4, min: 1 };
const D: PropSpec = { name: "d", kind: "int", default: 256, min: 1 };
const HEADS: PropSpec = { name: "heads", kind: "int", default: 4, min: 1 };
const KV: PropSpec = { name: "kv", kind: "int", default: 2, min: 1 };
const FFN: PropSpec = { name: "ffn", kind: "int", default: 1024, min: 1 };

/**
 * layerStack: repeat-N marker. LOCKED decision — counts ONLY the outer
 * norms pNorms((2N+1)*d); inner body params come from the explicitly
 * wired layer nodes in the graph, never from the stack.
 */
export const layerStack: LayerSpec = {
  kind: "layerStack",
  label: "Layer Stack",
  summary: "Repeat-N stack marker: outer norms only ((2N+1)*d); body params live in the wired layer nodes.",
  inputs: [X],
  outputs: [{ name: "out", label: "Hidden" }],
  props: [DEPTH, D, HEADS, KV, FFN],
  inferShape(_props, inputs) {
    return { ...requireIn(inputs, 0, "layerStack", X) };
  },
  paramCount(props, _out) {
    return pNorms({
      d: numProp("d", props.d, D),
      layers: numProp("depth", props.depth, DEPTH),
    });
  },
};
