diff --git a/mex/scripts/eval_mex.py b/mex/scripts/eval_mex.py
new file mode 100644
index 0000000..d4e5edf
--- /dev/null
+++ b/mex/scripts/eval_mex.py
@@ -0,0 +1,196 @@
+# mex/scripts/eval_mex.py — Task 7: exact-match eval vs measured trivial baselines.
+"""μ0 eval: per-task exact-match on held-out prompts (no training-data reuse).
+
+Loads runs/mex/<task>/final (config.yaml if present, else the committed
+configs/mex_<task>.yaml; model.safetensors or any *.safetensors shard),
+greedy-decodes after the task prompt prefix, and compares the continuation
+up to the first newline with the held-out target. Decoding uses the
+mex.src.vocab.CharVocab id mapping (our own per-char encoding) — no
+AutoTokenizer needed. Reports exact_match plus the task's trivial baseline,
+measured (not assumed) over the same held-out mix.
+
+Usage:
+    & .\.venv\Scripts\python.exe mex\scripts\eval_mex.py x1|x2|x3|x4|control|all
+    [--limit N]   # debug subset (default: full 500/2000-item test sets)
+"""
+from __future__ import annotations
+
+import argparse
+import json
+import sys
+from collections import Counter
+from pathlib import Path
+
+import torch
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT))
+
+from mex.src.tasks import arith, structure, strops  # same seeds/formats as packing
+from mex.src.vocab import CharVocab
+
+RUNS = {"x1": "x1", "x2": "x2", "x3": "x3", "x4": "x4", "control": "control"}
+CONFIGS = {"x1": "mex_x1", "x2": "mex_x2", "x3": "mex_x3",
+           "x4": "mex_x4", "control": "mex_control"}
+
+
+def load(task: str):
+    """Build the model for runs/mex/<task>/final and load its weights.
+
+    Config resolution: run/config.yaml first (train.py saves it via
+    save_pretrained), else the committed configs/mex_<task>.yaml. Weights:
+    model.safetensors, else any *.safetensors in the dir; a missing set is a
+    hard error — the eval runs after Task 6 training, never before.
+    """
+    import yaml
+    import torch
+    from safetensors.torch import load_file
+
+    from src.model import build_model
+
+    run = ROOT / "runs" / "mex" / task / "final"
+    cfg_path = run / "config.yaml"
+    if not cfg_path.exists():
+        cfg_path = ROOT / "configs" / f"{CONFIGS[task]}.yaml"
+    if not cfg_path.exists():
+        raise FileNotFoundError(f"no config for task {task!r}: tried "
+                                f"{run / 'config.yaml'} and {cfg_path}")
+    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
+
+    weights = run / "model.safetensors"
+    if not weights.exists():
+        shards = sorted(run.glob("*.safetensors"))
+        if not shards:
+            raise FileNotFoundError(
+                f"no .safetensors under {run} — Task 6 (training) has not run "
+                f"yet; eval_mex.py needs the trained final dir")
+        weights = shards[0]
+    state = load_file(str(weights))
+
+    model = build_model(cfg, vocab_size=cfg["tokenizer"]["vocab_size"])
+    missing, unexpected = model.load_state_dict(state, strict=False)
+    # lm_head.weight is tied to embed_tokens (same storage) and omitted by
+    # safetensors saves of tied models (src/model.py load_finetune_init rule).
+    bad_missing = [k for k in missing if k != "lm_head.weight"]
+    if bad_missing or unexpected:
+        raise RuntimeError(
+            f"weight mismatch for {task}: missing={bad_missing} "
+            f"unexpected={sorted(unexpected)}")
+    model.eval()
+    # Training builds the model with use_cache=False; generation needs it on.
+    model.config.use_cache = True
+    return cfg, model
+
+
+@torch.no_grad()
+def exact_match(model, prompts: list[str], targets: list[str]) -> float:
+    """Greedy-decode each prompt; hit iff the first decoded line == target."""
+    voc = CharVocab()
+    nl = voc.vocab["\n"]
+    ctx = int(model.config.max_position_embeddings)
+    hits = 0
+    for p, t in zip(prompts, targets):
+        ids = voc.encode(p)[-ctx:]
+        # Generate past the target length so an unterminated line can never
+        # fake a match by truncation; eos (newline) stops early anyway.
+        max_new = min(ctx, len(voc.encode(t)) + 2)
+        out = model.generate(torch.tensor([ids]), max_new_tokens=max_new,
+                             do_sample=False, pad_token_id=voc.vocab["<pad>"],
+                             eos_token_id=nl)
+        pred = voc.decode(out[0][len(ids):]).split("\n", 1)[0]
+        hits += int(pred.strip() == t.strip())
+    return hits / len(prompts)
+
+
+def _mode_frac(targets: list[str], pool: list[str]) -> float:
+    """Fraction of targets equal to the mode (most frequent) of pool.
+
+    Counter.most_common breaks count ties by first-encounter order —
+    deterministic across processes (a max(set(...)) tie-break would flip
+    with PYTHONHASHSEED; measured ties exist, e.g. x2 '62'/'76' at 77).
+    """
+    mode = Counter(pool).most_common(1)[0][0]
+    return sum(1 for x in targets if x == mode) / len(targets)
+
+
+def samples(t: str, limit: int | None = None) -> tuple[list[str], list[str], float]:
+    """Rebuild the SAME held-out prompts the generators produced (seed=42),
+    plus this task's pre-registered trivial baseline, measured over the
+    actual (possibly --limit-truncated) test mix."""
+    if t == "x1":
+        lines = (ROOT / "data" / "mex" / "x1" / "test.txt").read_text(
+            encoding="utf-8").splitlines()
+        if limit:
+            lines = lines[:limit]
+        prompts = [ln.split("|", 1)[0] + "|" for ln in lines]
+        targets = [ln.split("|", 1)[1] for ln in lines]
+        # Trivial = echo the bare word. build_x1_words.py's filter requires
+        # voc strictly longer than bare, so a bare echo never matches the
+        # held-out vocalization — ~0 by construction, measured here anyway.
+        trivial = sum(1 for tar, ln in zip(targets, lines)
+                      if tar == ln.split("|", 1)[0]) / len(targets)
+        return prompts, targets, trivial
+    if t == "x2":
+        d = arith(seed=42, n_val=200, n_test=500)
+        test = d["test"][:limit] if limit else d["test"]
+        prompts = [ln.split("|", 1)[0] + "|" for ln in test]
+        targets = [ln.split("|", 1)[1] for ln in test]
+        # Trivial = always answer the mode of the TRAIN answers.
+        train_targets = [ln.split("|", 1)[1] for ln in d["train"]]
+        return prompts, targets, _mode_frac(targets, train_targets)
+    if t == "x3":
+        d = structure(seed=42, n_val=200, n_test=500)
+        test = d["test"][:limit] if limit else d["test"]
+        prompts, targets = [], []
+        for ln in test:
+            seq, label = ln.rstrip("\n").split("\n")
+            prompts.append(seq + "\n")
+            targets.append(label)
+        # Trivial = always answer the mode of the TRAIN labels.
+        train_labels = [ln.rstrip("\n").split("\n")[1] for ln in d["train"]]
+        return prompts, targets, _mode_frac(targets, train_labels)
+    if t == "x4":
+        d = strops(seed=42, n_val=200, n_test=500)
+        test = d["test"][:limit] if limit else d["test"]
+        prompts = [ln.split("|", 1)[0] + "|" for ln in test]
+        targets = [ln.split("|", 1)[1] for ln in test]
+        # Trivial = identity: echo the source back (prompt form 'mode:src|').
+        # Measured over the ACTUAL test mix: it matches exactly the lines
+        # whose target equals the echoed source (copy always, rev/sort only
+        # when the transform is a fixed point). Targets keep the line's
+        # trailing newline; strip it before comparing.
+        trivial = sum(1 for p, x in zip(prompts, targets)
+                      if p.split(":", 1)[1][:-1] == x.strip()) / len(targets)
+        return prompts, targets, trivial
+    raise ValueError(f"unknown task {t!r}")
+
+
+def main() -> None:
+    ap = argparse.ArgumentParser(description="mex exact-match eval")
+    ap.add_argument("task", choices=[*RUNS, "all"], default="all", nargs="?")
+    ap.add_argument("--limit", type=int, default=None,
+                    help="debug: evaluate only the first N prompts")
+    args = ap.parse_args()
+    todo = list(RUNS) if args.task == "all" else [args.task]
+    for t in todo:
+        run = ROOT / "runs" / "mex" / RUNS[t] / "final"
+        if t == "control":  # one report, per-task breakdown
+            _, model = load(t)
+            report = {}
+            for sub in ("x1", "x2", "x3", "x4"):
+                prompts, targets, triv = samples(sub, args.limit)
+                report[sub] = {"exact_match": exact_match(model, prompts, targets),
+                               "trivial_baseline": triv}
+        else:
+            _, model = load(t)
+            prompts, targets, triv = samples(t, args.limit)
+            report = {"exact_match": exact_match(model, prompts, targets),
+                      "trivial_baseline": triv}
+        run.mkdir(parents=True, exist_ok=True)
+        (run / "mex_eval.json").write_text(
+            json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
+        print(RUNS[t], json.dumps(report, ensure_ascii=False))
+
+
+if __name__ == "__main__":
+    main()
