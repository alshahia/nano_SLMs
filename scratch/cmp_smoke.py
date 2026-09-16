from pathlib import Path
p = Path("models/e19/tashkeel-350m-v2/smoke3.pred.txt").read_text(encoding="utf-8").splitlines()
r = Path("models/e19/inputs/smoke3.ref.txt").read_text(encoding="utf-8").splitlines()
b = Path("models/e19/inputs/smoke3.bare.txt").read_text(encoding="utf-8").splitlines()
for i in range(len(b)):
    print("--", i, "BARE :", b[i][:90])
    print("--", i, "PRED :", p[i][:110] if i < len(p) else "<missing>")
    print("--", i, "REF  :", r[i][:90])