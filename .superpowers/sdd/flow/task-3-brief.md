# Task 3 brief — requirements verbatim

## Task 3: Node registry

**Files:** Create server/nodes.py; expand test_*.py (test_registry.py).
- [ ] Step 1: failing test: 6 kinds exactly; each exposes ports [{name,direction,type,burst-format}] & props keys & gate.
- [ ] Step 2: implement: dict NODES:
  kind: dataset     out:[cleaned: "raw-dir: dataset name/rows"] gate: none
  kind: prepare     in:"raw-dir"→out:"cleaned-dir"  props:{rows, val_fraction, min_chars}
  kind: tokenize    in:"cleaned-dir"→out:"shard-dir" props:{seq_len, vocab}
  kind: train       in:"shard-dir"→out:"ckpt-dir"   props:{preset,steps,lr_preset}  gate:"gpu"
  kind: eval        in:"ckpt-dir"→out:"report"      gate:"gpu"
  kind: infer       in:"ckpt-dir"                   render-only, gate:"gpu/cpu"
  + validate_props(kind,props) checking only key-existence and finite numbers.
- [ ] Step 3: unittest PASS, commit "flow: node registry".

## Orchestrator additions (binding, from Task 2 review)
- Task 3's registry test/fixtures must VERIFY the lazy hook: after nodes.py exists, a fromPort not in the kind's output ports is rejected by graph_schema (registry becomes source of truth for BOTH toPort and fromPort; if graph_schema currently skips fromPort-vs-outputs, that check is added in THIS task with a test).
- Add a one-line unittest for a graph whose edges key is entirely missing (valid: treated as []).
- Keep VALID_KINDS and PORTS (kind -> {in:[names], out:[names]}) exported from flow/server/nodes.py exactly as graph_schema expects (lazy import of flow.server.nodes).
