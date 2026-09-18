diff --git a/mex/scripts/pack.py b/mex/scripts/pack.py
new file mode 100644
index 0000000..ec7c9f2
--- /dev/null
+++ b/mex/scripts/pack.py
@@ -0,0 +1,70 @@
+"""Pack each \u03bc0 task's raw .txt into uint32 PackedDataset shards.
+
+src/data.py contract: shards are uint32 id streams; train.py loads
+'train_*.bin' + 'val_*.bin' from data.tokens_dir and slices blocks of
+seq_len = model.ctx. Lines are concatenated; newline chars are IN-vocab.
+Block boundary = mid-task is fine: the causal LM learns the format either way.
+
+NOTE (equal tokens, ME-D5): the control's train stream is the UNION of every
+task's train + val text, so control train tokens == sum(expert train tokens)
++ sum(expert val tokens consumed by each expert's val_0000.bin) by
+construction. gen_data caps are fixed (Tasks 2/3), so the control is ~4x
+each expert only in PARAMETERS, not tokens; the \u03bc0 report lists the actual
+token counts of the five runs side by side. Each expert's val_0000.bin stays
+held-out REAL blocks (never seen in that expert's train); test.txt stays
+unseen by packing entirely.
+"""
+from __future__ import annotations
+
+import sys
+from pathlib import Path
+
+import numpy as np
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT))
+
+from mex.src.vocab import CharVocab
+
+TASKS = ["x1", "x2", "x3", "x4"]
+CTX = 96  # mu0 context window (model.ctx)
+
+
+def pack(split_files: list[Path], out_prefix: Path, ctx: int) -> int:
+    voc = CharVocab()
+    ids: list[int] = []
+    for f in split_files:
+        ids.extend(voc.encode(f.read_text(encoding="utf-8")))
+    arr = np.asarray(ids, dtype=np.uint32)
+    shard = out_prefix  # single venue, tiny data
+    arr.tofile(shard.with_suffix(".bin"))
+    print(f"packed {shard.with_suffix('.bin')} : {arr.size} ids = {arr.size // ctx} blocks")
+    return int(arr.size)
+
+
+def main() -> None:
+    for t in TASKS:
+        src = ROOT / "data" / "mex" / t
+        tdir = src / "tokens"  # tokens live beside raw under tokens_dir convention
+        tdir.mkdir(parents=True, exist_ok=True)
+        pack([src / "train.txt"], tdir / "train_0000", ctx=CTX)
+        pack([src / "val.txt"] if (src / "val.txt").exists() else [src / "test.txt"],
+             tdir / "val_0000", ctx=CTX)
+    # control = union of every task's train + val text
+    ctrl = ROOT / "data" / "mex" / "control"
+    ctdir = ctrl / "tokens"
+    ctdir.mkdir(parents=True, exist_ok=True)
+    concat = []
+    for t in TASKS:
+        for k in ("train", "val"):
+            p = ROOT / "data" / "mex" / t / f"{k}.txt"
+            if p.exists():
+                concat.append(p)
+    pack(concat, ctdir / "train_0000", ctx=CTX)
+    pack([ROOT / "data" / "mex" / t / "val.txt" for t in TASKS
+          if (ROOT / "data" / "mex" / t / "val.txt").exists()],
+         ctdir / "val_0000", ctx=CTX)
+
+
+if __name__ == "__main__":
+    main()
diff --git a/mex/tests/test_params.py b/mex/tests/test_params.py
new file mode 100644
index 0000000..69937c6
--- /dev/null
+++ b/mex/tests/test_params.py
@@ -0,0 +1,61 @@
+# mex/tests/test_params.py
+"""Param-budget acceptance test for the ME expert/control pair (ME-D2/D5).
+
+Pins the budgets against the REAL model: llama_params() is the exact
+decomposition of src/model.py's LlamaForCausalLM (tied embeddings, no
+biases, RoPE parameter-free) and is asserted equal to the autograd sum
+sum(p.numel()) of build_model() so the formula can never drift from the
+shipped architecture (lesson 59: param anchors belong to tests).
+"""
+import sys
+from pathlib import Path
+
+sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
+
+from mex.src.vocab import char_ids
+
+EXPERT = {"layers": 2, "hidden": 80, "heads": 4, "kv_heads": 2, "ffn": 320}
+CONTROL = {"layers": 2, "hidden": 160, "heads": 4, "kv_heads": 2, "ffn": 640}
+VOCAB = len(char_ids())  # 97
+
+
+def llama_params(cfg, vocab):
+    """Exact parameter count of the real LlamaForCausalLM (src/model.py).
+
+    Per layer: q d*d, k kvd*d, v kvd*d, o d*kvd (kvd = kv_heads * head_dim;
+    GQA shares kv across head groups) -> 2*d*d + 2*d*kvd; SwiGLU MLP
+    gate/up/down = 3*d*f; two RMSNorms = 2*d. Top: tied lm_head/embed
+    vocab*d + final norm d. No biases anywhere; RoPE holds no parameters.
+    """
+    d, f, L = cfg["hidden"], cfg["ffn"], cfg["layers"]
+    kvd = cfg["kv_heads"] * (d // cfg["heads"])
+    attn = 2 * d * d + 2 * (d * kvd)
+    mlp = 3 * d * f
+    per_layer = attn + mlp + 2 * d
+    return L * per_layer + vocab * d + d
+
+
+def test_expert_in_band():
+    p = llama_params(EXPERT, VOCAB)
+    assert 100_000 <= p <= 300_000, p
+
+
+def test_control_within_5pct_of_4x_expert():
+    pe = llama_params(EXPERT, VOCAB)
+    pc = llama_params(CONTROL, VOCAB)
+    assert abs(pc - 4 * pe) <= 0.05 * 4 * pe, (pe, pc)
+
+
+def test_formula_matches_real_model():
+    """Pin the closed form to the shipped architecture (Task 4 Step 2)."""
+    from src.model import build_model
+
+    def cfg(hidden, ffn):
+        return {"model": {"layers": 2, "hidden": hidden, "heads": 4,
+                          "kv_heads": 2, "ffn": ffn, "ctx": 96,
+                          "tie_embeddings": True}}
+
+    for spec in (EXPERT, CONTROL):
+        model = build_model(cfg(spec["hidden"], spec["ffn"]), vocab_size=VOCAB)
+        real = sum(p.numel() for p in model.parameters())
+        assert real == llama_params(spec, VOCAB), (spec, real)
