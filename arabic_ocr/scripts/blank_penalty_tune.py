"""Tune the CTC blank penalty on muharaf_val, then report it on every test set.

Discipline: the penalty is selected ONLY on data/hf/muharaf/validation logits
(muharaf_val) and then applied unchanged to the held-out sets. Runs on the cached
teacher and adapt11700 logits, CPU only.
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(".")
sys.path.insert(0, str(ROOT / "arabic_ocr" / "models" / "muharaf_ocr"))
sys.path.insert(0, str(ROOT / "arabic_ocr" / "scripts"))

from submission_code.ocr_helpers import greedy_ctc_decode  # noqa: E402
from finetune_muharaf import CKPT_PATH, load_ctc_backbone  # noqa: E402


def lev(a, b):
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def score(path, charset, delta):
    npz = np.load(path, allow_pickle=True)
    data, offs, refs = npz["data"], npz["offsets"], [str(r) for r in npz["refs"]]
    logp = data.astype(np.float32)
    if delta:
        logp[:, charset.blank_id] -= delta
    hyps = []
    for i in range(len(offs) - 1):
        raw = np.argmax(logp[offs[i]:offs[i + 1]], axis=-1).tolist()
        hyps.append(charset.decode(greedy_ctc_decode(raw, blank_id=charset.blank_id)))
    nref = max(1, sum(len(r) for r in refs))
    return (100.0 * sum(lev(h, r) for h, r in zip(hyps, refs)) / nref,
            100.0 * sum(len(h) for h in hyps) / nref)


_, charset, _ = load_ctc_backbone(str(CKPT_PATH), device="cpu")
L = ROOT / "arabic_ocr/runs/stage05e/logits"
print("logits dirs: %s" % sorted(p.name for p in L.iterdir() if p.is_dir()), flush=True)

for tag in ["teacher", "adapt11700"]:
    vp = L / tag / "muharaf_val.npz"
    if not vp.exists():
        print("%s: no muharaf_val cache - skipped" % tag)
        continue
    sweep = [(d,) + score(vp, charset, d) for d in [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]]
    best = min(sweep, key=lambda r: r[1])
    print("\n%s VAL sweep: %s" % (tag, " ".join("d=%.2f:%.2f" % (d, c) for d, c, _ in sweep)))
    print("%s -> chosen delta %.2f (val CER %.2f)" % (tag, best[0], best[1]), flush=True)
    for st in ["muharaf_val", "muharaf_test", "khatt_teklia_test", "isippt_bench", "khatt_bench"]:
        p = L / tag / (st + ".npz")
        if not p.exists():
            continue
        c0, e0 = score(p, charset, 0.0)
        c1, e1 = score(p, charset, best[0])
        print("   %-18s delta0 %5.2f (emit %.1f%%) -> delta* %5.2f (emit %.1f%%)  %+.2f pp"
              % (st, c0, e0, c1, e1, c1 - c0), flush=True)
