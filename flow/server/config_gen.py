"""Config generator for the flow/ MVP (Task 5).

Bridges a validated .flow.json graph to the repo's EXISTING config
format (the webui train-tab contract, same wrapper via run_custom.py):
a linear dataset -> prepare -> tokenize -> train chain produces a
configs/flow_<slug>.yaml whose key structure is copied verbatim from
webui/app.py build_config / configs/smoke.yaml (never invented keys).

Public API:

- build_config(g) -> dict
    Pure function: enforces the linear-chain mapping, validates the
    document with flow.server.graph_schema plus flow.server.nodes.validate_props
    per node, and returns the nested config dict. Raises ValueError with
    human-readable reasons on any violation (nothing is ever written).

- generate(g, out_dir=None) -> str
    Calls build_config, then writes YAML (deterministic byte structure for
    future diffing) to <out_dir>/flow_<slug>.yaml and fsyncs. out_dir
    defaults to the repo's configs/; tests inject tempfile dirs and never
    write there. Returns the full written path.
"""

import os
from pathlib import Path

import yaml

from flow.server import graph_schema, nodes
from flow.server.flows import _SLUG_RE

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIGS_DIR = REPO_ROOT / "configs"

# Real key-name source of truth: webui/app.py PRESETS / LR_PRESETS
# (dims copied verbatim from the shipped configs).
PRESETS = {
    "Small (~12M, smoke)": dict(layers=4, hidden=256, heads=4, kv_heads=2,
                                ffn=1024, accum=32, ctx_choices=[256, 512]),
    "Medium (~101M, pilot)": dict(layers=12, hidden=768, heads=12, kv_heads=4,
                                  ffn=2048, accum=32, ctx_choices=[512]),
    "Large (~226M, target)": dict(layers=16, hidden=1024, heads=16, kv_heads=4,
                                  ffn=4096, accum=16, ctx_choices=[512, 1024]),
}
LR_PRESETS = {"Pretrain 4e-4": 4.0e-4, "Conservative 2e-4": 2.0e-4,
              "Fine-tune 3e-5": 3.0e-5}
TOKENIZER_NAME = "codellama/CodeLlama-7b-hf"
SHARD_TOKENS = 8000000

# The only execution chain the MVP maps to a config. Branching is rejected
# cleanly (never silently ignored) until the future F5 execution task.
CHAIN = ["dataset", "prepare", "tokenize", "train"]

_LINEAR_MSG = (
    "flow/%s: linear chains only - the MVP maps exactly one linear chain "
    "(linear chain mapping: dataset->prepare->tokenize->train) to a config; "
    "branching graphs run via advanced YAML only in this MVP (future F5 "
    "execution)"
)

# Child kind -> (upstream kind required, the output port that feeds it).
_DEPENDENCIES = [
    ["train", "tokenize", "shard-dir"],
    ["tokenize", "prepare", "cleaned-dir"],
    ["prepare", "dataset", "raw-dir"],
]


def _slug(name) -> str:
    """Return the validated run-name slug (flows.py regex, not reexported
    logic); every rejection names 'slug' for a stable error substring."""
    if not isinstance(name, str):
        raise ValueError("flow name: meta.name must be a slug string, got %r"
                         % (name,))
    if "/" in name or chr(92) in name or ".." in name:
        raise ValueError(
            "flow name: %r is not a slug (contains a path separator or '..')" 
            "- path traversal is not allowed" % (name,))
    if not _SLUG_RE.match(name):
        raise ValueError(
            "flow name: %r is not a slug - lowercase [a-z0-9-]{1,64} required"
            % (name,))
    return name


class _LinearChain:
    """Structural view: branching/merging/foreign kinds, or linear path."""

    def __init__(self, g):
        self.node_list = [n for n in g["graph"].get("nodes", [])
                          if isinstance(n, dict)]
        self.by_id = {n.get("id"): n for n in self.node_list
                      if isinstance(n.get("id"), str) and n["id"]}
        self.in_edges = {}   # node id -> list of (edge, from_id)
        self.out_edges = {}  # node id -> list of (edge, to_id)
        for edge in g["graph"].get("edges", []) or []:
            if not isinstance(edge, dict):
                continue  # graph_schema already reported the shape error
            frm, to = edge.get("from"), edge.get("to")
            if frm in self.by_id and to in self.by_id:
                self.out_edges.setdefault(frm, []).append((edge, to))
                self.in_edges.setdefault(to, []).append((edge, frm))

    def linear(self) -> bool:
        """True when nothing structurally branches. Missing chain kinds are
        NOT a linearity failure here: the dependency walk reports exactly
        which required upstream node (and port) is absent."""
        if not self.node_list:
            return False  # no chain at all is not a linear chain
        kinds = [n.get("kind") for n in self.node_list]
        if any(k not in CHAIN for k in kinds if k is not None):
            return False  # node kinds outside the train chain
        present = [k for k in kinds if k is not None]
        if len(set(present)) != len(present):
            return False  # duplicated chain kind is not a linear mapping
        for _nid, edges in self.out_edges.items():
            if len(edges) > 1:
                return False  # branching
        for _nid, edges in self.in_edges.items():
            if len(edges) > 1:
                return False  # merge (diamond)
        return True


def _build_chain(g):
    """Return {kind: node} for the dataset->prepare->tokenize->train chain.

    Raises the linear-only ValueError for branching graphs and the
    missing-input ValueError naming each absent required upstream node.
    """
    view = _LinearChain(g)
    if not view.linear():
        raise ValueError(_LINEAR_MSG % (g.get("meta") or {}).get("name"),)
    train = next((n for n in view.node_list if n.get("kind") == "train"),
                 None)
    if train is None:
        raise ValueError(
            "train: no train node found - the MVP maps exactly one "
            "linear chain (linear chain mapping: dataset->prepare->tokenize"
            "->train) to a config")
    chain = [train]
    # Walk backwards: every link must be the exact kind/port pair.
    for _child_kind, dep_kind, port in _DEPENDENCIES:
        child = chain[-1]
        ins = view.in_edges.get(child.get("id"), [])
        if not ins:
            raise ValueError(
                "%s requires upstream %s node providing %s; none found "
                "(node '%s')" % (child.get("kind"), dep_kind, port,
                                 child.get("id")))
        parent_id = ins[0][1]
        parent = view.by_id.get(parent_id, {})
        if parent.get("kind") != dep_kind:
            raise ValueError(
                "%s requires upstream %s node providing %s; node '%s' has "
                "kind %r instead (node '%s')"
                % (child.get("kind"), dep_kind, port, parent_id,
                   parent.get("kind"), child.get("id")))
        chain.append(parent)
    chain.reverse()  # dataset, prepare, tokenize, train
    return {kind: node for kind, node in zip(CHAIN, chain)}


def build_config(g) -> dict:
    """Validate graph + props and return the nested config dict (pure).

    Raises ValueError (joined graph-schema reasons, registry prop reasons,
    linear-chain structural errors, or missing knob errors).
    """
    malformed = not (isinstance(g, dict)
                     and isinstance(g.get("graph"), dict)
                     and isinstance(g["graph"].get("nodes"), list))
    if malformed:
        # Degenerate document: the schema reasons are the honest answer.
        errors = list(graph_schema.validate(g))
        raise ValueError("\n".join(errors))

    # 1. Linear-chain structural mapping (BEFORE schema error emission so a
    #    branching graph gets the linear-only message, not a port quote).
    _build_chain(g)

    # 2. Document schema (graph_schema.validate) + per-node registry props -
    #    the same dual-validator boundary flows.py uses at save.
    errors = list(graph_schema.validate(g))
    for node in g["graph"]["nodes"]:
        if not isinstance(node, dict):
            continue  # graph_schema already reported the shape error
        for reason in nodes.validate_props(node.get("kind"),
                                           node.get("props")):
            errors.append("graph.nodes[%s]: %s" % (node.get("id", "?"),
                                                   reason))
    if errors:
        raise ValueError("\n".join(errors))

    # 3. Run-name slug - flows.py slug rule reused, not reimplemented.
    slug = _slug((g.get("meta") or {}).get("name"))

    # 4. Parse the chain nodes into knobs. Misses produce named errors.
    chain = _build_chain(g)
    train = chain["train"]
    tprops = train.get("props", {})
    if "steps" not in tprops:
        raise ValueError("steps: missing - train node '%s' requires the "
                         "steps knob" % (train.get("id"),))

    ds_node = chain["dataset"]
    label = ds_node.get("label")
    if not isinstance(label, str) or not label.strip():
        raise ValueError(
            "dataset name: node '%s' has no label - the dataset node's "
            "label is the HF dataset name in this MVP" % ds_node.get("id"))
    ds_name = label.strip()
    pp = chain["prepare"]["props"]
    tp = chain["tokenize"]["props"]
    for kind, props in (("prepare", pp), ("tokenize", tp)):
        for key in sorted(nodes.PROPS[kind]):
            if key not in props:
                raise ValueError(
                    "%s: missing - %s node '%s' requires the %s knob"
                    % (key, kind, chain[kind].get("id"), key))

    preset_name = tprops["preset"]
    if not isinstance(preset_name, str):
        raise ValueError("preset: expected a string preset name, got %r"
                         % (preset_name,))
    if preset_name not in PRESETS:
        raise ValueError("preset: unknown preset %r" % (preset_name,))
    p = PRESETS[preset_name]
    lr_name = tprops["lr_preset"]
    if not isinstance(lr_name, str):
        raise ValueError("lr_preset: expected a string LR preset name, "
                         "got %r" % (lr_name,))
    if lr_name not in LR_PRESETS:
        raise ValueError("lr_preset: unknown lr_preset %r" % (lr_name,))
    lr = LR_PRESETS[lr_name]

    steps = int(tprops["steps"])
    ctx = int(tp["seq_len"])
    if ctx not in p["ctx_choices"]:
        raise ValueError("ctx %d not valid for preset %r (choices %s)"
                         % (ctx, preset_name, p["ctx_choices"]))

    # 5. Nested config - key structure copied verbatim from webui build_config
    #    minus the interactive-only data_mode knob (matches shipped
    #    configs/smoke.yaml key structure exactly).
    cfg = {
        "name": slug,
        "tokenizer": {"name": TOKENIZER_NAME, "vocab_size": int(tp["vocab"])},
        "model": {"layers": p["layers"], "hidden": p["hidden"],
                  "heads": p["heads"], "kv_heads": p["kv_heads"],
                  "ffn": p["ffn"], "ctx": ctx, "dropout": 0.0,
                  "tie_embeddings": True},
        "data": {"dataset_candidates": [{"name": ds_name}],
                 "rows": int(pp["rows"]),
                 "val_fraction": float(pp["val_fraction"]),
                 "dedupe": True, "min_chars": int(pp["min_chars"]),
                 "shard_tokens": SHARD_TOKENS,
                 "raw_dir": "data/%s/raw" % slug,
                 "tokens_dir": "data/%s/tokens" % slug},
        "train": {"output_dir": "runs/%s" % slug,
                  "final_dir": "runs/%s/final" % slug,
                  "max_steps": steps, "batch": 1, "eval_batch": 4,
                  "accum": p["accum"], "lr": lr, "scheduler": "cosine",
                  "warmup_steps": max(10, steps // 20),
                  "weight_decay": 0.1, "max_grad_norm": 1.0,
                  "logging_steps": 50, "eval_steps": 500, "save_steps": 500,
                  "save_total_limit": 3, "fp16": True, "grad_ckpt": True,
                  "optim": "adamw_torch", "dataloader_num_workers": 0,
                  "seed": 42},
        "eval": {"max_new_tokens": 64,
                 "prompts": ["def fibonacci(n):", "class Stack:"]},
    }
    return cfg


def generate(g, out_dir=None) -> str:
    """Validate, then write configs/flow_<slug>.yaml and fsync; return path.

    Nothing is touched on disk until build_config accepts the graph.
    out_dir defaults to the repo's configs/; tests pass tempfile dirs ONLY.
    """
    cfg = build_config(g)  # every validation happens here, no I/O yet
    slug = cfg["name"]
    target = Path(out_dir) if out_dir is not None else DEFAULT_CONFIGS_DIR
    target.mkdir(parents=True, exist_ok=True)
    path = target / ("flow_" + slug + ".yaml")
    payload = yaml.safe_dump(cfg, sort_keys=False, allow_unicode=False)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())  # data-preservation rule: durable before OK
    return str(path)
