"""Scratch (Milestone D): validate configs/next_pretrain.yaml without GPU.
- section/key-set comparison vs configs/target.yaml (real keys only)
- mix-mode detection mirrors prepare_data.py's rule
- CPU model build -> param count (expect ~100.7M, the recorded pilot size)
- step arithmetic: 4100 steps x (1024*1*32) tokens/step
Run: .venv/Scripts/python data/legacy_check/validate_next_pretrain.py
"""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

new_cfg = yaml.safe_load((ROOT / "configs" / "next_pretrain.yaml").read_text(encoding="utf-8"))
tgt = yaml.safe_load((ROOT / "configs" / "target.yaml").read_text(encoding="utf-8"))
pil = yaml.safe_load((ROOT / "configs" / "pilot.yaml").read_text(encoding="utf-8"))

fails = []

def check(name, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'} {name} {detail}")
    if not cond:
        fails.append(name)

# 1) top-level sections identical to target.yaml
check("sections", sorted(new_cfg.keys()) == sorted(tgt.keys()),
      f"new={sorted(new_cfg.keys())} target={sorted(tgt.keys())}")
check("name", new_cfg["name"] == "next_pretrain")
check("tokenizer keys", sorted(new_cfg["tokenizer"]) == sorted(tgt["tokenizer"]))
check("tokenizer name", new_cfg["tokenizer"]["name"] == tgt["tokenizer"]["name"])
check("model keys", sorted(new_cfg["model"]) == sorted(tgt["model"]))
check("data keys", sorted(new_cfg["data"]) == sorted(tgt["data"]),
      f"new={sorted(new_cfg['data'])}")
check("train keys", sorted(new_cfg["train"]) == sorted(tgt["train"]),
      f"new={sorted(new_cfg['train'])}")
check("eval keys", sorted(new_cfg["eval"]) == sorted(tgt["eval"]))

# 2) model dims = pilot dims except ctx 1024
m_expect = dict(pil["model"]); m_expect["ctx"] = 1024
check("model dims == pilot dims @ctx1024", new_cfg["model"] == m_expect,
      str(new_cfg["model"]))

# 3) mix-mode detection + candidates
cands = new_cfg["data"]["dataset_candidates"]
mix = any("target_rows" in c for c in cands)
check("mix detected", mix)
check("all candidates carry target_rows", all("target_rows" in c for c in cands))
check("stack-smol uses data_dir", cands[0].get("data_dir") == "data/python"
      and "config" not in cands[0], str(cands[0]))
check("starcoderdata uses data_dir", cands[1].get("data_dir") == "python"
      and "config" not in cands[1], str(cands[1]))
expected = [("code-search-net/code_search_net", "python", 15000),
            ("nickrosh/Evol-Instruct-Code-80k-v1", None, 5000)]
got = [(c["name"], c.get("config"), c["target_rows"]) for c in cands[2:]]
check("2 remaining candidates exact", got == expected, str(got))
check("sum target_rows", sum(c["target_rows"] for c in cands) == 230000)

# 4) train block values
t = new_cfg["train"]
check("tok/step", 1024 * t["batch"] * t["accum"] == 32768)
check("max_steps x tok/step", t["max_steps"] * 32768 == 134348800,
      f"{t['max_steps']}*32768={t['max_steps']*32768}")
check("optim 8bit", t["optim"] == "adamw_bnb_8bit")
check("save mult of eval", t["save_steps"] % t["eval_steps"] == 0,
      f"save={t['save_steps']} eval={t['eval_steps']}")
check("batch/accum", (t["batch"], t["accum"]) == (1, 32))

# 5) CPU model build (no GPU touched)
from src.model import build_model
model = build_model(new_cfg, vocab_size=32768)
n = sum(p.numel() for p in model.parameters())
check("param count ~100.7M (pilot)", abs(n / 1e6 - 100.7) < 1.5,
      f"{n/1e6:.1f}M")
del model

print(f"RESULT: {'ALL PASS' if not fails else 'FAILURES: ' + ', '.join(fails)}")
sys.exit(0 if not fails else 1)