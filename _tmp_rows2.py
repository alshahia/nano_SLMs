import re
txt = open("TASKS.md", encoding="utf-8").read()
m = re.search(r"^\| 40 \|.*8k\/12k\/16k.*", txt, re.M)
print(m.group(0)[:1200] if m else "NOT FOUND")