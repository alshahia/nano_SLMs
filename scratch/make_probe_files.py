import unicodedata, re
from pathlib import Path
import json
MK = re.compile("[" + "".join(chr(c) for c in range(0x64a, 0x653)) + chr(0x670) + "".join(chr(c) for c in range(0x6d6, 0x6ee)) + "]")
texts = json.loads(Path("scratch/probe_texts.json").read_text(encoding="utf-8"))
out = Path("research/user_probe")
out.mkdir(parents=True, exist_ok=True)
for k in ("1", "2", "3"):
    t = texts[k]
    bare = unicodedata.normalize("NFC", MK.sub("", t))
    ref = unicodedata.normalize("NFC", t)
    (out / ("probe" + k + "_bare.txt")).write_text(bare + "\n", encoding="utf-8")
    (out / ("probe" + k + "_ref.txt")).write_text(ref + "\n", encoding="utf-8")
    print("probe" + k, "bare", len(bare), "ref", len(ref))
