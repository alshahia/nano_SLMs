import pathlib
row = pathlib.Path("scratch/e17_row.txt").read_text(encoding="utf-8").strip()
p = pathlib.Path("research/EXPERIMENTS.md")
s = p.read_text(encoding="utf-8")
marker = "| E-17-RESTORED-NOT-ACTUAL-ROW - I will replace via pwsh\n"
assert marker in s, "marker missing"
s = s.replace(marker, row + "\n")
p.write_text(s, encoding="utf-8")
print("E-17 restored, len", len(row))