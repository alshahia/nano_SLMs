import random, os
os.makedirs("models/e19/inputs", exist_ok=True)
ref = [l for l in open("scratch/stage2b2500/abdou_test_pred.ref.txt", encoding="utf-8").read().splitlines() if l.strip()]
import re
BAND = "[\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0670\u0674\u06d6-\u06ed]"
strip = lambda t: re.sub(BAND, "", t)
held = ref[::20]
open("models/e19/inputs/abdou_heldout.bare.txt", "w", encoding="utf-8").write("\n".join(strip(t) for t in held) + "\n")
open("models/e19/inputs/abdou_heldout.ref.txt", "w", encoding="utf-8").write("\n".join(held) + "\n")
print("abdou held-out lines:", len(held))
rng = random.Random(2026)
for gate, src in [("fadel2500", "models/e19/inputs/fadel2500.ref.txt"), ("sadeed2500", "models/e19/inputs/sadeed2500.ref.txt"), ("wn2014", "models/e19/inputs/wn2014.ref.txt")]:
    lines = [l for l in open(src, encoding="utf-8").read().splitlines() if l.strip()][:200]
    shuf = [" ".join(rng.sample(l.split(), len(l.split()))) for l in lines]
    open(f"models/e19/inputs/{gate}.shuf.bare.txt", "w", encoding="utf-8").write("\n".join(strip(t) for t in shuf) + "\n")
    open(f"models/e19/inputs/{gate}.shuf.ref.txt", "w", encoding="utf-8").write("\n".join(shuf) + "\n")
    print("shuffled slice", gate, len(shuf))