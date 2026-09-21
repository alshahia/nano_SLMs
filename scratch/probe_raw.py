import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
p = r"E:\python_projects\nano_SLMs\data\langid\schemer\train.tsv"
raw = open(p, encoding="utf-8").read()[:1200]
print(repr(raw))
