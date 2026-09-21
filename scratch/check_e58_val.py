import numpy as np, torch, sys
sys.path.insert(0, r"E:/python_projects/nano_SLMs")
sys.path.insert(0, r"E:/python_projects/nano_SLMs/mex")
from transformers import LlamaForCausalLM
from safetensors.torch import load_file
from mex.src.vocab import CharVocab
from pathlib import Path
R = Path("E:/python_projects/nano_SLMs/runs/mex/dia2g_15head")
tr = LlamaForCausalLM.from_pretrained(str(R)).to("cuda").eval()
tr.load_state_dict(load_file(str(R / "model.safetensors")), strict=True)
head = torch.nn.Linear(1280, 15).to("cuda")
head.load_state_dict(load_file(str(R / "head15.safetensors")))
X = np.load(R / "_xv.npy"); Y = np.load(R / "_yv.npy")
B = 128; ok = tot = 0; per = np.zeros(15); cnt = np.zeros(15)
with torch.no_grad(), torch.amp.autocast("cuda", dtype=torch.float16):
    for bi in range(0, len(X) - B + 1, B):
        xb = torch.from_numpy(X[bi:bi+B].astype(np.int64)).to("cuda")
        lb = torch.from_numpy(Y[bi:bi+B].astype(np.int64)).to("cuda")
        h = tr(input_ids=xb, output_hidden_states=True).hidden_states[-1]
        m = lb != -100
        p = head(h.float()).argmax(-1)
        eq = p[m] == lb[m]
        tys = lb[m].cpu().numpy(); eqs = eq.cpu().numpy()
        for c in range(15):
            sel = tys == c
            if sel.sum(): per[c] += eqs[sel].sum(); cnt[c] += sel.sum()
        ok += int(eq.sum()); tot += int(m.sum())
print("per-base acc:", ok / tot)
for c in range(15):
    if cnt[c]: print(c, round(per[c] / cnt[c], 4), int(cnt[c]))
