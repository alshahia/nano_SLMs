"""Batched external-model inference for E-19 bake-off (CPU/GPU)."""
import argparse, os, re, sys, time
cwd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(cwd)

def read_lines(p):
    return [l.rstrip("\n") for l in open(p, encoding="utf-8") if l.strip()]

def strip_marks(t):
    return re.sub("[\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0670\u0674\u06d6-\u06ed]", "", t)

PY_PROMPT = "\u0642\u0645 \u0628\u062a\u0634\u0643\u064a\u0644 \u0647\u0630\u0627 \u0627\u0644\u0646\u0635" + ":\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)   # HF id or local dir
    ap.add_argument("--pred", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--batch", type=int, default=12)
    a = ap.parse_args()
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    tok = AutoTokenizer.from_pretrained(a.model)
    model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=torch.float16, device_map="cuda" if torch.cuda.is_available() else "cpu")
    model.eval()
    pad_id = tok.pad_token_id or tok.eos_token_id
    lines = read_lines(a.pred)
    if a.limit:
        lines = lines[:a.limit]
    t0 = time.time()
    outs = []
    tok.padding_side = "left"
    for s in range(0, len(lines), a.batch):
        batch_in = [strip_marks(t) for t in lines[s:s+a.batch]]
        prompts = []
        for t in batch_in:  # truncate input to keep the mamba2 chunk-scan temporaries small
            prompts.append(PY_PROMPT + t)
        cap = max(min(400, max(64, int(1.6 * max(len(t) for t in batch_in)))) , 64)
        cap = max(min(1600, max(48, 3 * max(len(t) for t in batch_in))), 80)
        enc = tok(prompts, return_tensors="pt", padding=True).to(model.device)
        with torch.no_grad():
            gen = model.generate(**enc, max_new_tokens=cap, do_sample=False, num_beams=1, pad_token_id=pad_id, eos_token_id=tok.eos_token_id)
        gen = gen[:, enc["input_ids"].shape[1]:]
        for i in range(len(batch_in)):
            outs.append(tok.decode(gen[i], skip_special_tokens=True).strip())
        done = min(s + a.batch, len(lines))
        rate = done / max(time.time() - t0, 1e-9)
        print(f"[{done}/{len(lines)}] {rate:.2f} lines/s", flush=True)
    open(a.out, "w", encoding="utf-8").write("\n".join(outs) + "\n")

main()