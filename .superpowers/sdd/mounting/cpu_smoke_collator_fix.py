"""CPU smoke for the mount.py collator fix (evidence for task-3 FIX REPORT).

Runs the REAL scripts/mount.py main() UNPATCHED on CPU against a throwaway
config copy (.superpowers/sdd/mounting/cpu_smoke_drill3.yaml - fp16 off,
torch optimizer, batch 2, throwaway output dir; configs/mount_fill_drill3.yaml
itself is untouched). Only two intercepts:
- torch.cuda.is_available forced False (NVML reports True on this box even
  though this smoke is forbidden to touch the GPU)
- Trainer.train captured + stopped -> trainer construction completes, no run

Then, for mode=fill (real config body) and mode=gate (yaml.safe_load override;
at eff_step 0 gate_strength==0 -> exact strength-0 skip path, no teacher
forward; drop/hybrid are config-blocked and only differ in schedules):
 1) train dataloader batch carries input_ids/teacher_ids/teacher_pad_mask
 2) ONE manual trainer.compute_loss(model, batch) train-branch call under
    torch.no_grad on CPU
 3) same batch through the eval branch (pure CE)
 4) prediction_step routing check (label_names) + model.forward spy (model
    receives ONLY input_ids/labels, never the teacher keys)
"""
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""   # smoke is CPU-only, no GPU touch
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
SMOKE_CFG = ".superpowers/sdd/mounting/cpu_smoke_drill3.yaml"
sys.argv = ["mount.py", "--config", SMOKE_CFG]

import torch
import transformers as TF
torch.cuda.is_available = lambda: False   # NVML reports True even with empty CVD; force CPU for main()

import yaml as Y
_real_sl = Y.safe_load
_override = [None]


def _sl(path):
    cfg = _real_sl(path)
    if _override[0] is not None:
        cfg["mount"]["mode"] = _override[0]
    return cfg


Y.safe_load = _sl

# NO dtype shim: the committed fix passes dtype=torch.float32 to the teacher
# from_pretrained in scripts/mount.py itself - this smoke verifies THAT path.

_captured = []


def _capture_train(self, *a, **kw):
    print("  [probe] args: type=%s pdtbs=%s fp16=%s device=%s"
          % (type(self.args).__name__, self.args.per_device_train_batch_size,
             self.args.fp16, self.args.device), flush=True)
    _captured.append(self)
    raise SystemExit(0)


TF.Trainer.train = _capture_train

from scripts.mount import main  # noqa: E402


def run(mode=None):
    _override[0] = mode
    try:
        main()
    except SystemExit:
        pass
    return _captured.pop()


def smoke(tag, tr):
    print("\n===== mode=" + tag + " =====", flush=True)
    print("collator.__name__ =", getattr(tr.data_collator, "__name__", type(tr.data_collator).__name__))
    assert getattr(tr.data_collator, "__name__", "") == "default_data_collator", "collator was wrapped/stripped"
    print("label_names =", tr.label_names)
    assert tr.label_names == ["input_ids"], tr.label_names
    batch = next(iter(tr.get_train_dataloader()))
    keys = sorted(batch.keys())
    assert keys == sorted(["input_ids", "teacher_ids", "teacher_pad_mask"]), keys
    for k in ("input_ids", "teacher_ids", "teacher_pad_mask"):
        print("  batch[%s]: shape=%s dtype=%s" % (k, tuple(batch[k].shape), batch[k].dtype))
    assert batch["input_ids"].shape == (2, 512), batch["input_ids"].shape
    assert batch["teacher_ids"].shape == (2, 512)
    assert batch["teacher_pad_mask"].dtype == torch.bool
    # eval routing: prediction_step's has_labels must be True so eval goes
    # through MountTrainer.compute_loss's pure-CE branch
    has_labels = all(batch.get(k) is not None for k in tr.label_names)
    assert has_labels, "eval would NOT route through compute_loss"
    print("  has_labels (prediction_step routing) =", has_labels)

    # spy on model.forward kwargs INSIDE compute_loss calls
    model = tr.model
    orig_fwd = model.forward
    seen = []

    def spy(**kw):
        seen.append(sorted(kw.keys()))
        return orig_fwd(**kw)

    model.forward = spy
    model.train()
    with torch.no_grad():
        tr_loss = tr.compute_loss(model, batch)
    print("  TRAIN compute_loss: loss=%.6f (shape=%s dtype=%s)"
          % (float(tr_loss), tuple(tr_loss.shape), tr_loss.dtype))
    model.eval()
    with torch.no_grad():
        ev_loss = tr.compute_loss(model, batch)
    print("  EVAL compute_loss : loss=%.6f (pure CE)" % float(ev_loss))
    model.forward = orig_fwd
    assert seen and all(c == ["input_ids", "labels"] for c in seen), seen
    print("  model.forward kwargs over %d call(s): %s" % (len(seen), seen[0]))
    print(tag + ": PASS")


smoke("fill", run(None))
smoke("gate", run("gate"))
print("\nALL CPU SMOKE STEPS: PASS")
