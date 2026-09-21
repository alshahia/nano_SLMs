import sys, numpy as np, torch, torch.nn as nn
from pathlib import Path
sys.path.insert(0, r"E:/python_projects/nano_SLMs")
from torch.utils.data import DataLoader
from transformers import LlamaForCausalLM, LlamaConfig
from safetensors.torch import load_file
sys.path.insert(1, r"E:/python_projects/nano_SLMs/mex")
from mex.src.vocab import CharVocab
ROOT = Path(r"E:/python_projects/nano_SLMs")
# reproduce the trainer's dataset exactly
import importlib.util
spec = importlib.util.spec_from_file_location("t60a", ROOT / "mex/scripts/train_e60a.py")
mod = importlib.util.module_from_spec(spec)
import unittest.mock as mk
# train_e60a calls main() at import bottom; guard: read class only
src = (ROOT / "mex/scripts/train_e60a.py").read_text(encoding="utf-8").replace("main();", "pass")
ns = {}
exec(compile(src, "train_e60a.py", "exec"), ns)
voc = CharVocab()
base_ids = {int(tid) for ch, tid in voc.vocab.items()
            if len(ch) == 1 and (0x621 <= ord(ch) <= 0x64A or 0x64B <= ord(ch) <= 0x652)}
tdir = ROOT / "data/diac/v3q/tokens"
val_ds = ns["V3QJoint"](tdir, 96, "val", base_ids)
from torch.utils.data import DataLoader
loader = DataLoader(val_ds, batch_size=256, shuffle=False, num_workers=0)
device = "cuda"
m = LlamaForCausalLM.from_pretrained(str(ROOT / "runs/mex/dia2j_e60a/final")).to(device).eval()
hd = torch.nn.Linear(320, 15).to(device); hd.load_state_dict(load_file(str(ROOT / "runs/mex/dia2j_e60a/final/head15.safetensors")))
correct = 0; total = 0
with torch.no_grad():
    for vb in loader:
        xi = vb["input_ids"].to(device)
        ob = m(input_ids=xi, output_hidden_states=True)
        pred = ob.hidden_states[-1].argmax(dim=-1).cpu()
        msk = vb["mark_labels"] >= 0
        correct += int((vb["mark_labels"][msk] == pred[msk]).sum()); total += int(msk.sum())
print("replicated in-loop metric:", round(correct / max(total, 1), 4), " on", total, "mark positions")
print("ns has V3QJoint:", "V3QJoint" in ns)
