import re, pathlib
def strip(t):
    return re.sub("[\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0670\u0674\u06d6-\u06ed]", "", t)
src = {
  "fadel2500": "runs/diac/stage2b2500/gate_probe/step2500_fadel_test_pred.ref.txt",
  "sadeed2500": "runs/diac/stage2b2500/gate_probe/step2500_sadeed25_pred.ref.txt",
  "wn2014": "runs/diac/stage2b2500/gate_probe/step2500_wikinews2014_pred.ref.txt",
  "abdou_stride5": "scratch/stage2b2500/abdou_test_pred.ref.txt",
}
outd = pathlib.Path("models/e19/inputs")
outd.mkdir(parents=True, exist_ok=True)
for k, p in src.items():
    lines = [l.strip() for l in open(p, encoding="utf-8") if l.strip()]
    if k == "abdou_stride5":
        lines = lines[::5]  # stride 5: keep the held-out sizable but benchable
    (outd / (k + ".bare.txt")).write_text("\n".join(strip(l) for l in lines) + "\n", encoding="utf-8")
    (outd / (k + ".ref.txt")).write_text("\n".join(l for l in lines) + "\n", encoding="utf-8")
    print(k, len(lines), "lines")