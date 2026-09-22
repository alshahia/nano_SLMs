import sys, time, torch
from pathlib import Path
from safetensors.torch import load_file
from transformers import LlamaConfig, LlamaForCausalLM
ROOT = Path("E:/python_projects/nano_SLMs"); sys.path.insert(0, str(ROOT))
src = (ROOT / "mex/scripts/train_e61b.py").read_text(encoding="utf-8").replace("main();", "pass")
ns = {}
exec(compile(src, "train_e61b.py", "exec"), ns)
tdir = ROOT / "data/diac/v3q/tokens"
val_ds = ns["V3QJoint"](tdir, 96, "val", set())
from mex.src.vocab import CharVocab
base_ids = {int(tid) for ch, tid in CharVocab().vocab.items() if len(ch) == 1 and (0x621 <= ord(ch) <= 0x64A or 0x64B <= ord(ch) <= 0x652)}
val_ds2 = ns["V3QJoint"](tdir, 96, "val", base_ids)
x = torch.as_tensor([val_ds2[i]["input_ids"].tolist() for i in range(8)], dtype=torch.long, device="cuda")
m4 = LlamaForCausalLM.from_pretrained(str(ROOT / "runs/mex/dia2j_e60a_a3/final")).to("cuda").eval()
with torch.no_grad(): r4 = m4(input_ids=x).logits.float()
del m4; torch.cuda.empty_cache()
lc = LlamaConfig(vocab_size=97, hidden_size=320, intermediate_size=1280, num_hidden_layers=8,
                 num_attention_heads=8, num_key_value_heads=2, max_position_embeddings=96, rms_norm_eps=1e-5, rope_theta=10000.0)
m8 = LlamaForCausalLM(lc).to("cuda").eval()
print("load_state_dict:", m8.load_state_dict(load_file(str(ROOT / "runs/mex/dia2j_e60a_a3/final/model.safetensors")), strict=False))
with torch.no_grad():
    for i in range(4, 8):
        m8.model.layers[i].self_attn.o_proj.weight.zero_()
        m8.model.layers[i].mlp.down_proj.weight.zero_()
    r8 = m8(input_ids=x).logits.float()
d = (r4 - r8).abs().max().item()
print(f"[probe] zero-loss identity max|dlogit| = {d:.6g} (bar 1e-2) -> {'PASS' if d < 1e-2 else 'FAIL'}")
m8.train()
opt = torch.optim.AdamW([p for p in m8.parameters() if p.requires_grad], lr=2e-4)
xs = torch.as_tensor([val_ds2[i]["input_ids"].tolist() for i in range(512)], dtype=torch.long, device="cuda")
n_train = sum(p.numel() for p in m8.parameters() if p.requires_grad)
torch.cuda.reset_peak_memory_stats(); t0 = time.time(); steps = 20
for i in range(steps):
    with torch.autocast("cuda", dtype=torch.float16):
        ob = m8(input_ids=x[:512], output_hidden_states=True); h = ob.hidden_states[-1]
    loss = ob.logits[:, :-1].float().reshape(-1, 97).pow(2).mean() + h.pow(2).mean() * 1e-6
    loss.backward(); opt.step(); opt.zero_grad()
torch.cuda.synchronize()
print(f"[probe] 8L trainable={n_train:,}; bs512 fwd+bwd {512*96/max((time.time()-t0)/steps,1e-9):.0f} tok_s; peak VRAM {torch.cuda.max_memory_allocated()/2**30:.2f} GiB")
