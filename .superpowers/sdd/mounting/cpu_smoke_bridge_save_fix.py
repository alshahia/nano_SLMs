"""CPU smoke for FIX #3: plain-list _mount_bridges (bridge dup-shard save crash)."""
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""   # CPU-only, no GPU touch
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import torch
from transformers import AutoModelForCausalLM, LlamaConfig

from src.mount import WrappedLayer, attach_mounts, detach_mounts

cfg = LlamaConfig(vocab_size=64, hidden_size=64, intermediate_size=128,
                  num_hidden_layers=4, num_attention_heads=4,
                  num_key_value_heads=2, max_position_embeddings=16)
m = AutoModelForCausalLM.from_config(cfg)
bridges = attach_mounts(m, teacher_layers=6)
assert len(bridges) == 4
assert [br.teacher_anchor for br in bridges] == [1, 2, 4, 5]
assert isinstance(m.model.layers[0], WrappedLayer)

bridge_names = [k for k, _ in m.named_parameters() if "bridge" in k]
assert [k for k in bridge_names if k.startswith("_mount_bridges")] == [], "dup _mount_bridges keys"
per_layer = []
for l in range(4):
    ks = [k for k in bridge_names if "layers.%d.bridge." % l in k]
    assert ks, "no bridge params for layer %d" % l
    per_layer.append(len(ks))
addr = {}
for k, p in m.named_parameters():
    i = id(p)
    assert i not in addr, "param appears TWICE: %r and %r" % (addr[i], k)
    addr[i] = k
print("1) named_parameters: %d bridge keys, zero _mount_bridges.*, per-layer %s, no addr dup" % (len(bridge_names), per_layer))

sd = m.state_dict()
assert [k for k in sd if k.startswith("_mount_bridges")] == [], "state_dict has _mount_bridges keys"
seen = {}
for k, v in sd.items():
    if isinstance(v, torch.Tensor):
        dp = v.data_ptr()
        assert dp not in seen, "state_dict dup pair: %r == %r" % (k, seen[dp])
        seen[dp] = k
print("2) state_dict: %d keys, zero dup data_ptr pairs" % len(sd))

ids = torch.randint(0, 64, (2, 16))
for br in bridges:
    br._strength = 0.5
    br._current_kv = torch.randn(2, 5, 64)
m(input_ids=ids, labels=ids).loss.backward()
assert any(br.a.grad is not None and br.a.grad.abs() > 0 for br in bridges), "a.grad must flow"
print("4) forward+backward OK: bridge a.grad nonzero")

m.zero_grad()
tmp = ROOT / "runs" / "_bridge_save_smoke.throwaway"
tmp.mkdir(parents=True, exist_ok=True)
try:
    m.save_pretrained(str(tmp))   # crashed before fix: duplicate tensor names
    from safetensors import safe_open
    hits = []
    for f in sorted(tmp.glob("*.safetensors")):
        with safe_open(str(f), framework="pt") as fh:
            hits += [k for k in fh.keys() if "bridge" in k]
    assert [k for k in hits if k.startswith("_mount_bridges")] == [], hits[:5]
    print("3) save_pretrained OK: %d safetensors bridge keys, all layered" % len(hits))
finally:
    shutil.rmtree(str(tmp), ignore_errors=True)

n_before = sum(p.numel() for p in m.parameters())
detach_mounts(m)
n_after = sum(p.numel() for p in m.parameters())
n_ref = sum(p.numel() for p in AutoModelForCausalLM.from_config(cfg).parameters())
assert n_after == n_ref
assert m._mount_bridges is None
print("5) detach restores exact original param set (%d == %d)" % (n_after, n_ref))
print("ALL CPU SMOKE STEPS: PASS")
