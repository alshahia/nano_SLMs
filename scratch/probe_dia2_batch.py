"""scratch/probe_dia2_batch.py - user-directed GPU smoke (E-57 killed for it).

Time + VRAM-profile dia2 trunk (49.8M params, ctx 96, fp16): train fwd+bwd at
batch 32/64/128/256, eval fwd-only (torch.no_grad) at batch 128/256/512/1024.
Outputs ms/it, k tok/s, peak GiB per size. Fresh LoRA on merged trunk.
"""
import sys, time
from pathlib import Path
import torch, yaml
from safetensors.torch import load_file
from peft import LoraConfig, get_peft_model
from transformers import LlamaForCausalLM

ROOT = Path("E:/python_projects/nano_SLMs")
sys.path.insert(0, str(ROOT))

model = LlamaForCausalLM.from_pretrained(str(ROOT / 'runs/mex/dia2d_scale/final')).to('cuda').eval()
sd = load_file(str(ROOT / 'runs/mex/dia2d_scale/final/model.safetensors'))
model.load_state_dict(sd, strict=True)
cfg = yaml.safe_load(open(ROOT / 'configs/dia2f_replay.yaml', encoding='utf-8'))
l = cfg['lora']
pe = LoraConfig(task_type='CAUSAL_LM', r=int(l['r']), lora_alpha=int(l['alpha']), target_modules=list(l['targets']))
model = get_peft_model(model, pe)
model.train()
seq = int(cfg['model']['ctx'])


def bench(bs, fwd, steps=6):
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    ids = torch.randint(0, 90, (bs, seq), device='cuda')
    att = torch.ones_like(ids)
    pm = None
    try:
        for k in range(steps):
            with (torch.no_grad() if fwd else torch.enable_grad()):
                loss = model(input_ids=ids, attention_mask=att, labels=ids).loss
            if not fwd:
                loss.backward()
                model.zero_grad(set_to_none=True)
            torch.cuda.synchronize()
            torch.cuda.empty_cache()
        t0 = time.perf_counter()
        for k in range(steps):
            with (torch.no_grad() if fwd else torch.enable_grad()):
                loss = model(input_ids=ids, attention_mask=att, labels=ids).loss
            if not fwd:
                loss.backward()
                model.zero_grad(set_to_none=True)
            torch.cuda.synchronize()
            pm = torch.cuda.max_memory_allocated()
        dt = (time.perf_counter() - t0) / steps
        print(f"{'eval' if fwd else 'train'} bs={bs}: {dt*1000:.0f} ms/it, {bs*seq/dt/1e3:.0f}k tok/s, peak {pm/2**30:.2f} GiB", flush=True)
        return True
    except torch.cuda.OutOfMemoryError:
        print(f"{'eval' if fwd else 'train'} bs={bs}: OOM", flush=True)
        torch.cuda.empty_cache()
        return False


torch.cuda.set_per_process_memory_fraction(0.95)
for bs in (32, 64, 128, 256):
    bench(bs, fwd=False)
model.eval()
for bs in (128, 256, 512, 1024):
    bench(bs, fwd=True)
