import subprocess, sys, json
from pathlib import Path
sys.path.insert(0, "diacritizer/scripts")
import postproc as PP

PY = Path(".venv/Scripts/python.exe")
GP = Path("runs/diac/stage2b2500/gate_probe")
PAIRS = [
    ("gold abdou_test", Path("scratch/stage2b2500/abdou_test_pred.txt"), Path("scratch/stage2b2500/abdou_test_pred.ref.txt")),
    ("gold fadel_test@2500", GP / "step2500_fadel_test_pred.txt", GP / "step2500_fadel_test_pred.ref.txt"),
    ("gold sadeed25@2500", GP / "step2500_sadeed25_pred.txt", GP / "step2500_sadeed25_pred.ref.txt"),
    ("gold wn2014@2500", GP / "step2500_wikinews2014_pred.txt", GP / "step2500_wikinews2014_pred.ref.txt"),
]
OUT = Path("scratch/postproc_ab")
OUT.mkdir(parents=True, exist_ok=True)

def run_eval(pred, ref):
    r = subprocess.run([str(PY), "-X", "utf8", "diacritizer/scripts/eval.py", "compare",
                        "--pred", str(pred), "--ref", str(ref)], capture_output=True, text=True)
    return json.loads(r.stdout)["aggregate"]["DER"] * 100

print("variant | abdou | fadel | sadeed | wn14")
rows = {"baseline": {}, "dedup": {}, "legality": {}}
for name, pred, ref in PAIRS:
    raw = pred.read_text(encoding="utf-8")
    variants = {"baseline": raw, "dedup": PP.dedup_marks(raw), "legality": PP.legality_repair(raw)}
    for vname, txt in variants.items():
        path = OUT / (pred.stem + "." + vname + ".txt")
        path.write_text(txt, encoding="utf-8")
        rows[vname][name] = run_eval(path, ref)
for vname in ("baseline", "dedup", "legality"):
    vals = rows[vname]
    line = " ".join(f"{vals.get(n, float(chr(110)+chr(97)+chr(110))):.2f}" for n in ("gold abdou_test", "gold fadel_test@2500", "gold sadeed25@2500", "gold wn2014@2500"))
    print(vname, line)