### Task 2: `webui/explorer.py` — dims math, block graph, two-level info (TDD)

**Files:**
- Create: `webui/explorer.py`
- Create: `tests/test_explorer.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_explorer.py` exactly:

```python
"""tests for webui/explorer.py — graph math validated against real models."""
import _common  # noqa: F401

import artifacts as A
import explorer as E
from _common import run

ROOT = A.ROOT
SMOKE = ROOT / "runs" / "smoke" / "final"
TARGET = ROOT / "runs" / "target" / "final"


def _smoke_dims_header():
    return A.hf_config_dims(SMOKE), A.safetensors_header(SMOKE)


def t_projected_formula_matches_all_three():
    gates = [("smoke", 12_323_072), ("pilot", 100_682_496), ("target", 226_526_208)]
    for phase, want in gates:
        dims = A.yaml_config_dims(A.phase_config(phase))
        got = E.projected_params(dims)
        assert got == want, (phase, got, want)


def t_build_graph_smoke_real():
    dims, header = _smoke_dims_header()
    blocks = E.build_graph(dims, header, label="smoke/final", lora=None)
    # tok + embed + 4 layers x 4 blocks + final norm + lm_head + logits
    assert len(blocks) == 2 + 4 * dims["layers"] + 3, len(blocks)
    assert blocks[0]["id"] == "tok" and blocks[-1]["id"] == "logits"
    embed = blocks[1]
    assert embed["params"] == 32768 * 256 and embed["real"] is True
    attn = next(b for b in blocks if b["kind"] == "attn")
    assert attn["params"] > 0 and attn["tensors"], "real attn tensors missing"
    assert all(b["plain"] and b["tech"] for b in blocks), "info text missing"


def t_build_graph_projected_flagged():
    dims = A.yaml_config_dims(A.phase_config("smoke"))
    blocks = E.build_graph(dims, None, label="smoke (config)", lora=None)
    # tok/logits need no header (real=True); tied lm_head + logits are 0-param
    assert [b["id"] for b in blocks if b["real"]] == ["tok", "logits"]
    assert [b["id"] for b in blocks
            if b["params"] == 0] == ["tok", "lm_head", "logits"]
    assert all(b["params"] > 0 for b in blocks
               if b["id"] not in ("tok", "lm_head", "logits"))


def t_kv_cache_token_target_16kib():
    dims = A.hf_config_dims(TARGET)
    kib = E.kv_cache_kib_per_token(dims)
    assert abs(kib - 16.0) < 0.1, kib  # measured on this machine


def t_shape_trace():
    dims, header = _smoke_dims_header()
    blocks = E.build_graph(dims, header, label="smoke/final", lora=None)
    walk = E.shape_walk(blocks)
    assert walk[0][1] == "[text]" and walk[-1][1] == "[1, 64, 32768]"
    mid = next(w for w in walk if w[0].endswith("attn"))
    assert mid[1] == f"[1, 64, {dims['hidden']}]", mid


if __name__ == "__main__":
    run({k[2:]: v for k, v in sorted(globals().items()) if k.startswith("t_")})
```

- [ ] **Step 2: Run to verify it fails**

Run: `& .\.venv\Scripts\python.exe tests\test_explorer.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'explorer'`.

- [ ] **Step 3: Write `webui/explorer.py`**

Create `webui/explorer.py` exactly:

```python
r"""Model Explorer data model: param math, block graph, two-level info.
Pure logic + data — no Gradio here (model_tab.py owns wiring). Every number
is computed live from artifacts (real headers when a checkpoint exists, the
projected formula otherwise, always flagged). Read-only, CPU-only.
"""
from __future__ import annotations

from pathlib import Path

from artifacts import module_param_totals

KIND_COLOR = {"tok": "#7c3aed", "embed": "#d97706", "norm": "#2563eb",
              "attn": "#6d28d9", "ffn": "#059669", "out": "#b45309"}


def head_dim(dims: dict) -> int:
    return dims["hidden"] // max(int(dims["heads"]), 1)


def projected_params(dims: dict) -> int:
    """Param formula; VERIFIED against the three real finals:
    smoke 12,323,072 / pilot 100,682,496 / target 226,526,208.
    (Same math as scripts/status.py estimate_params; kept local so tests
    don't pull TensorBoard.)"""
    h = int(dims["hidden"])
    hd, kv = head_dim(dims), int(dims["kv_heads"])
    q = int(dims["heads"]) * hd * h
    k = v = kv * hd * h
    o = q
    swiglu = 3 * h * int(dims["ffn"])
    per_layer = q + k + v + o + swiglu + 2 * h          # 2 RMSNorms
    embed = int(dims["vocab"]) * h
    lm = 0 if dims["tie"] else int(dims["vocab"]) * h
    return embed + int(dims["layers"]) * per_layer + h + lm


def kv_cache_kib_per_token(dims: dict) -> float:
    """2 (K and V) x layers x kv_heads x head_dim x 2 B (fp16), in KiB.
    Target = 16.0 KiB/token (independently measured on this machine)."""
    b = 2 * int(dims["layers"]) * int(dims["kv_heads"]) * head_dim(dims) * 2
    return b / 1024


def _block(bid, kind, title, layer, params, real, tensors, io, pairs, plain, tech):
    return {"id": bid, "kind": kind, "title": title, "layer": layer,
            "params": int(params), "real": bool(real), "tensors": tensors,
            "io": io, "config_pairs": pairs, "plain": plain, "tech": tech}


def build_graph(dims: dict, header: dict | None, label: str, lora: dict | None):
    """Ordered block list for the selected model. Real per-block params and
    tensor names come from the safetensors header when present; otherwise
    the projected formula (every block flagged real=False)."""
    h = int(dims["hidden"])
    seq = min(int(dims["ctx"]) or 64, 64)
    L = int(dims["layers"])
    hd, heads, kv = head_dim(dims), int(dims["heads"]), int(dims["kv_heads"])
    vocab = int(dims["vocab"])
    totals = module_param_totals(header) if header else {}
    real = bool(header)
    blocks: list[dict] = []

    def fmt(n: int) -> str:
        return f"{n:,}"

    blocks.append(_block(
        "tok", "tok", "Tokenizer (CodeLlama 32k)", None, 0, True, {},
        ("[text]", f"[1, {seq}] ids"),
        [("vocab_size", vocab), ("tokenizer", "codellama/CodeLlama-7b-hf")],
        f"Turns your text into one of {vocab:,} token IDs the model knows. "
        "A sentencepiece vocabulary trained for code — indentation and "
        "underscores are single tokens.",
        f"sentencepiece BPE, vocab_size {vocab:,}. Not a learned module: no "
        "params. The Trace box runs the REAL tokenizer files from the "
        "checkpoint."))

    emb_params = totals.get("embed", vocab * h)
    emb_dtype = next(iter((header or {}).values()), {"dtype": "fp32"})["dtype"]
    blocks.append(_block(
        "embed", "embed", "Token embedding (lookup table)", None, emb_params,
        real, {k: v for k, v in (header or {}).items() if "embed_tokens" in k},
        (f"[1, {seq}]", f"[1, {seq}, {h}]"),
        [("vocab", vocab), ("hidden", h), ("tied_lm_head", dims["tie"])],
        f"A lookup table: token ID -> a row of {h} learned numbers. "
        + ("TIED with the output layer: the same table reads tokens in and "
           "scores tokens out — halves the biggest cost in a small model. "
           if dims["tie"] else "Separate from the output layer here. "),
        f"params {fmt(emb_params)} = vocab {vocab:,} x hidden {h}, dtype "
        f"{emb_dtype}. Row i of the table is what token i becomes."))

    for i in range(L):
        pre = totals.get(f"L{i}.input_layernorm", h)
        blocks.append(_block(
            f"L{i}.pre_attn_norm", "norm",
            f"Layer {i} - RMSNorm (pre-attention)", i, pre, real, {},
            (f"[1, {seq}, {h}]",) * 2,
            [("rms_eps", dims["rms_eps"]), ("hidden", h)],
            "Rescales each token's vector to a stable size before attention. "
            "The cheaper cousin of LayerNorm — no mean subtraction, just RMS. "
            "Keeps deep stacks trainable.",
            f"weight [{h}] ({fmt(pre)} params), eps {dims['rms_eps']}. "
            "y = x / sqrt(mean(x^2) + eps) * weight."))
        attn_params = totals.get(f"L{i}.self_attn", 0) or (
            heads * hd * h + 2 * kv * hd * h + heads * hd * h)
        attn_tensors = ({k: v for k, v in (header or {}).items()
                         if k.startswith(f"model.layers.{i}.self_attn")}
                        if header else {})
        blocks.append(_block(
            f"L{i}.attn", "attn",
            f"Layer {i} - GQA attention (RoPE, causal, +residual)", i,
            attn_params, real, attn_tensors,
            (f"[1, {seq}, {h}]", f"[1, {seq}, {h}]"),
            [("heads", heads), ("kv_heads", kv), ("head_dim", hd),
             ("rope_theta", dims["rope_theta"]), ("seq", seq)],
            f"Every token looks back at earlier tokens and decides what to "
            f"copy. {heads} query heads share {kv} key/value heads (GQA) — the "
            f"K/V side is cut {heads // max(kv, 1)}x, saving memory at almost "
            "no quality cost. Causal: a token never sees the future. RoPE "
            "rotates vectors by position so order is baked in without a "
            "position table.",
            f"q_proj [{h}x{heads * hd}] ({fmt(heads * hd * h)}), k/v_proj "
            f"[{h}x{kv * hd}] ({fmt(kv * hd * h)} each), o_proj "
            f"[{heads * hd}x{h}]. rope_theta {dims['rope_theta']}. KV-cache "
            f"{kv_cache_kib_per_token(dims):.1f} KiB/token for THIS model "
            "(2 x layers x kv_heads x head_dim x 2 B). SDPA backend "
            "(sm_75: no flash-attn)."))
        post = totals.get(f"L{i}.post_attention_layernorm", h)
        blocks.append(_block(
            f"L{i}.post_attn_norm", "norm", f"Layer {i} - RMSNorm (pre-FFN)",
            i, post, real, {}, (f"[1, {seq}, {h}]",) * 2,
            [("rms_eps", dims["rms_eps"])],
            "Same stabilizer again, before the FFN. Two norms per block is "
            "the pre-norm layout — it is what makes residual streams "
            "trainable at depth.",
            f"weight [{h}] ({fmt(post)} params), eps {dims['rms_eps']}."))
        ffn_params = totals.get(f"L{i}.mlp", 0) or (3 * h * int(dims["ffn"]))
        ffn_tensors = ({k: v for k, v in (header or {}).items()
                        if k.startswith(f"model.layers.{i}.mlp")}
                       if header else {})
        blocks.append(_block(
            f"L{i}.ffn", "ffn", f"Layer {i} - SwiGLU FFN", i, ffn_params,
            real, ffn_tensors,
            (f"[1, {seq}, {h}]", f"[1, {seq}, {h}]"),
            [("ffn", dims["ffn"]), ("hidden", h)],
            f"The 'thinking' MLP: expands each token to {dims['ffn']} numbers, "
            f"filters through a gate, back to {h}. Most of the model's "
            "parameters live here, and this is where token knowledge is "
            "stored.",
            f"gate/up [{h}x{dims['ffn']}] + down [{dims['ffn']}x{h}] = "
            f"3*h*ffn = {fmt(3 * h * int(dims['ffn']))}. SwiGLU: "
            "down( SiLU(gate(x)) * up(x) )."))

    blocks.append(_block(
        "final_norm", "norm", "Final RMSNorm", None,
        totals.get("model.norm", h), real, {},
        (f"[1, {seq}, {h}]",) * 2, [("rms_eps", dims["rms_eps"])],
        "One last rescale before scoring tokens. Same job as the layer norms.",
        f"weight [{h}] ({fmt(totals.get('model.norm', h))} params)."))

    lm_params = totals.get("lm_head", 0) or (0 if dims["tie"] else vocab * h)
    lm_tensors = ({k: v for k, v in (header or {}).items()
                   if k.startswith("lm_head")} if header else {})
    blocks.append(_block(
        "lm_head", "out", "lm_head (output projection)", None, lm_params,
        real and bool(lm_params), lm_tensors,
        (f"[1, {seq}, {h}]", f"[1, {seq}, {vocab}]"),
        [("vocab", vocab), ("tied", dims["tie"])],
        ("TIED with the embedding table — zero extra parameters; the same "
         "lookup table is transposed to score every token."
         if dims["tie"] and not lm_params else
         f"Projects each token to {vocab:,} raw scores (logits)."),
        f"logits = h @ W_out ({fmt(lm_params) if lm_params else 'tied: 0'} "
        f"params; output [1, {seq}, {vocab:,}]). Softmax comes later, at "
        "sampling time."))

    blocks.append(_block(
        "logits", "out", "Logits -> next token", None, 0, True, {},
        (f"[1, {seq}, {vocab}]", "[1, vocab] probs"),
        [("vocab", vocab)],
        "The final vector is compared against every row of the vocabulary: "
        "softmax turns scores into probabilities. The Chat tab's temperature "
        "/ top-p / top-k knobs all act on this distribution.",
        "argmax = greedy; temperature / top-p / top-k = sampling. Trained "
        "against cross-entropy on the true next token."))

    if lora:
        for b in blocks:
            if b["kind"] in ("attn", "ffn"):
                b["plain"] += (f" LoRA r={lora['r']} adapters are trained on "
                               "this block's projections; base weights frozen.")
    return blocks


def shape_walk(blocks):
    """[(id, in_shape, out_shape)] in graph order — the prompt-trace walk."""
    return [(b["id"], b["io"][0], b["io"][1]) for b in blocks]


def tokenize_trace(run_path: Path | None, text: str) -> str:
    """REAL CodeLlama tokenizer from the checkpoint dir (local files only,
    never the network). Markdown: token count + id list. No weights loaded."""
    if run_path is None:
        return ("*Trace needs a trained run (it loads the tokenizer files "
                "from the checkpoint directory). Pick 'From trained run'.*")
    if not text.strip():
        return "*Type some text to trace.*"
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(str(run_path))
    ids = tok(text, add_special_tokens=False).input_ids
    toks = tok.convert_ids_to_tokens(ids)
    shown = list(zip(toks, ids))[:24]
    lines = [f"**{len(ids)} tokens** (showing first {len(shown)}):", ""]
    lines += [f"`{t!r}` -> id {i}" for t, i in shown]
    if len(ids) > len(shown):
        lines.append(f"... +{len(ids) - len(shown)} more")
    lines += ["", "These IDs index rows of the embedding table — that is "
              "the model's actual input."]
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to green**

Run: `& .\.venv\Scripts\python.exe tests\test_explorer.py`
Expected: `5/5 checks passed`. If `t_projected_formula_matches_all_three` is off by a hair, read the header keys and fix the formula — do NOT loosen the gates beyond ±1%.

- [ ] **Step 5: Commit**

```powershell
git add webui/explorer.py tests/test_explorer.py
git commit -m "feat(webui): U12 explorer - param math (validated 12.3M/100.7M/226.5M), block graph, two-level info"
```

---


