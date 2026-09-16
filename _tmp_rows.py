import re
txt = open("TASKS.md", encoding="utf-8").read()
for n in [11,12,13,19,20,29,36,38,40]:
    m = re.search(r"^\| %d \|.*" % n, txt, re.M)
    if m: print("ROW", n, "::", m.group(0)[:900].replace(chr(92), "/"), "\n")