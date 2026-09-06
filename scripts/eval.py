"""Post-run evaluation: val loss + perplexity + generation samples.

Run: .venv/Scripts/python scripts/eval.py --config configs/smoke.yaml [--ckpt DIR]

With an SFT config (eval.instructions_file + data.template present, e.g.
configs/sft_t1.yaml) it additionally runs the C12 Tier-1 instruction eval:
greedy + sampled generations over held-out instructions and the ast.parse
pass-rate (plan §3.3 success criterion). The forgetting guard is the same
script twice on the same config: --ckpt runs/target/final (before SFT) vs
--ckpt runs/sft_t1/final (after); the CSN val-loss delta is the regression gate.
"""
import argparse
import json
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--ckpt", default=None, help="model dir; default runs/<name>/final")
    ap.add_argument("--max_new_tokens", type=int, default=None,
                    help="overrides eval.max_new_tokens in the config (default 64)")
    args = ap.parse_args()

    import torch
    import yaml
    from torch.utils.data import DataLoader
    from transformers import AutoModelForCausalLM, AutoTokenizer

    from src.data import PackedDataset
    from sft_data import extract_code, parses_as_python

    cfg = yaml.safe_load((ROOT / args.config).read_text(encoding="utf-8"))
    seq_len = int(cfg["model"]["ctx"])
    ckpt = Path(args.ckpt) if args.ckpt else ROOT / cfg["train"]["final_dir"]
    if not ckpt.is_dir():
        raise SystemExit(f"model dir not found: {ckpt} (train first)")

    tok = AutoTokenizer.from_pretrained(str(ckpt))
    model = AutoModelForCausalLM.from_pretrained(str(ckpt))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device).eval()
    print(f"[eval] model={ckpt} device={device}", flush=True)

    # CLI flag > config > legacy default (old configs all set 64, so behavior
    # for smoke/pilot/target is unchanged).
    gen_len = (args.max_new_tokens if args.max_new_tokens is not None
               else int(cfg["eval"].get("max_new_tokens", 64)))

    val_ds = PackedDataset((ROOT / cfg["data"]["tokens_dir"]).glob("val_*.bin"), seq_len)
    loader = DataLoader(val_ds, batch_size=8, shuffle=False)
    total_nll, total_tok = 0.0, 0
    with torch.no_grad():
        for batch in loader:
            ids = batch["input_ids"].to(device)
            labels = batch["labels"].to(device)
            out = model(input_ids=ids, labels=labels)
            n = labels.numel()
            total_nll += float(out.loss) * n
            total_tok += n
    avg_nll = total_nll / max(total_tok, 1)
    ppl = math.exp(min(avg_nll, 20))  # clamp: untrained models overflow exp()
    print(f"[eval] val_loss={avg_nll:.4f} perplexity={ppl:.2f} tokens={total_tok}",
          flush=True)

    samples = {}
    for prompt in cfg["eval"]["prompts"]:
        inputs = tok(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=gen_len,
                                 do_sample=False, pad_token_id=tok.eos_token_id)
        samples[prompt] = tok.decode(out[0], skip_special_tokens=True)
        print(f"--- prompt: {prompt!r}\n{samples[prompt]}\n", flush=True)

    # C12 Tier-1 instruction eval (only for SFT configs that declare it)
    instruction_eval = None
    instr_rel = cfg["eval"].get("instructions_file")
    template = cfg["data"].get("template")
    if instr_rel and template:
        instr_path = ROOT / instr_rel
        if not instr_path.exists():
            print(f"[eval] instructions file missing, skipping instruction eval: "
                  f"{instr_path}", flush=True)
        else:
            n_max = int(cfg["eval"].get("n_instructions", 50))
            temperature = float(cfg["eval"].get("sample_temperature", 0.8))
            instructions = []
            with instr_path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        instructions.append(json.loads(line)["instruction"])
            instructions = instructions[:n_max]
            print(f"[eval] instruction eval: {len(instructions)} held-out "
                  f"instructions, greedy + temp={temperature}, "
                  f"max_new_tokens={gen_len}", flush=True)
            room = max(seq_len - gen_len, 16)
            greedy_ok, sample_ok, fails = [], [], []
            for i, instr in enumerate(instructions):
                prompt = template.format(instruction=instr)
                inputs = tok(prompt, return_tensors="pt", truncation=True,
                             max_length=room).to(model.device)
                base_len = inputs["input_ids"].shape[1]
                with torch.no_grad():
                    g = model.generate(**inputs, max_new_tokens=gen_len,
                                       do_sample=False,
                                       pad_token_id=tok.eos_token_id)
                    s = model.generate(**inputs, max_new_tokens=gen_len,
                                       do_sample=True, temperature=temperature,
                                       top_p=0.95,
                                       pad_token_id=tok.eos_token_id)
                g_text = tok.decode(g[0][base_len:], skip_special_tokens=True)
                s_text = tok.decode(s[0][base_len:], skip_special_tokens=True)
                g_ok = parses_as_python(extract_code(g_text))
                s_ok = parses_as_python(extract_code(s_text))
                greedy_ok.append(g_ok)
                sample_ok.append(s_ok)
                if not (g_ok and s_ok):
                    fails.append({"instruction": instr,
                                  "greedy": g_text, "sampled": s_text})
                if (i + 1) % 10 == 0:
                    print(f"[eval] instructions {i + 1}/{len(instructions)}: "
                          f"greedy {sum(greedy_ok)}/{i + 1}, "
                          f"sampled {sum(sample_ok)}/{i + 1}", flush=True)
            instruction_eval = {
                "n": len(instructions),
                "greedy_ast_pass_rate": sum(greedy_ok) / max(len(instructions), 1),
                "sampled_ast_pass_rate": sum(sample_ok) / max(len(instructions), 1),
                "temperature": temperature,
                "failed_examples": fails[:5],
            }
            print(f"[eval] ast.parse pass-rate: greedy "
                  f"{instruction_eval['greedy_ast_pass_rate']:.2f}, sampled "
                  f"{instruction_eval['sampled_ast_pass_rate']:.2f}", flush=True)

    report = {"ckpt": str(ckpt), "val_loss": avg_nll, "perplexity": ppl,
              "samples": samples}
    if instruction_eval is not None:
        report["instruction_eval"] = instruction_eval
    out_path = Path(ckpt) / "eval_report.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"[eval] report written: {out_path}", flush=True)


if __name__ == "__main__":
    main()
