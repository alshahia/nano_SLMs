import io

# TASKS row 90 -> done with honest verdict; add new row 92 for user-gated DA-2 improvement rungs
p = 'TASKS.md'
s = io.open(p, encoding='utf-8').read()
old = s.splitlines()

import re
lines = s.splitlines()
out = []
for i, L in enumerate(lines):
    if L.startswith('| 90 |'):
        L = "| 90 | DA-2 Emo-analogue (ar+en emoji suggestion, 76 classes) - **done** | `done` | closed 2026-09-19 honest: D1/D3/D4/D5 PASS, D2 FAIL (beats prior +2.7/+3.5 pp but not the pre-registered top-1 bars); E-44; report DA2_REPORT.md | research/desert_ant_recreation/DA2_REPORT.md |"
    out.append(L)
s = '\n'.join(out) + '\n'

# insert continuation row after row 90's line
marker = "| 90 | DA-2 Emo-analogue"
idx = s.index(marker)
eol = s.index('\n', idx)
row91 = "\n| 92 | DA-2b (user-gated): close D2 - bigger Arabic emoji corpus (mine/research), tiny transformer head, weighted CE | `pending` | USER-GATED | DA2_REPORT.md 'what would close D2' |"
s = s[:eol] + row91 + s[eol:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('TASKS updated')