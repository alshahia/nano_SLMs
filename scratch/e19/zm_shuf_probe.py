import sys, time, re
sys.path.insert(0, "models/e19/zmahood-src/src")
from diacritize import Diacritizer

runner = sys.argv[1] if len(sys.argv) > 1 else "all"

BLOCKS = {
  "heldout":  ("models/e19/inputs/abdou_heldout.bare.txt", "models/e19/abdou_heldout.zmahood.pred.txt"),
  "fadelshuf":("models/e19/inputs/fadel2500.shuf.bare.txt", "models/e19/fadel.shuf.zmahood.pred.txt"),
  "sadeedshuf":("models/e19/inputs/sadeed2500.shuf.bare.txt", "models/e19/sadeed.shuf.zmahood.pred.txt"),
  "wnshuf":   ("models/e19/inputs/wn2014.shuf.bare.txt", "models/e19/wn.shuf.zmahood.pred.txt"),
}
src = "models/e19/zmahood-src/src"
cm = {name: (read_in, out) for name, (read_in, out) in BLOCKS.items()}

import os
os.chdir("E:/python_projects/nano_SLMs")

if runner == "all" or runner == "heldout":
    d = Diacritizer.from_pretrained(no_cache=True)
    lines = [l.rstrip("\n") for l in open(BLOCKS["heldout"][0], encoding="utf-8") if l.strip()]
    t0 = time.time(); outs = []
    for i, l in enumerate(lines):
        outs.append(d.diacritize(l))
        if (i+1) % 500 == 0: print(f"heldout {i+1}/{len(lines)} {((i+1)/(time.time()-t0)):.1f} l/s", flush=True)
    open(BLOCKS["heldout"][1], "w", encoding="utf-8").write("\n".join(outs) + "\n")
    print("heldout done %.0fs" % (time.time()-t0), flush=True)

if runner == "all" or runner == "shuf":
    d = Diacritizer.from_pretrained(no_cache=True)
    for name in ["fadelshuf", "sadeedshuf", "wnshuf"]:
        src_in, out = BLOCKS[name]
        lines = [l.rstrip("\n") for l in open(src_in, encoding="utf-8") if l.strip()]
        outs = [d.diacritize(l) for l in lines]
        open(out, "w", encoding="utf-8").write("\n".join(outs) + "\n")
        print(name, "done", flush=True)