import io
p = 'TASKS.md'
s = io.open(p, encoding='utf-8').read()
old = "| 92 | DA-2b (user-gated): close D2 - bigger Arabic emoji corpus (mine/research), tiny transformer head, weighted CE | `pending` | USER-GATED | DA2_REPORT.md 'what would close D2' |"
new = "| 92 | DA-2b arms a/b/c (34.5k-row Arabic emoji corpus + tiny transformer + weighted CE/LS) - **done** | `done` | closed 2026-09-19 honest: arm (a) +5-18pp ar (test 0.4063 top-1 w/ transformer, prior+0.05 ar PASS, ar crossed the E-44 sub-bar), arm (b) is the skill lever, arm (c) honest FAIL (rare-class flooding; bag+c stuck at val 0.12), 2x-prior bar still unmet; int8 transformer 1.686 MiB / 1.75 ms / agree 99.8 pct - PASS D4 | research/desert_ant_recreation/DA2B_REPORT.md |"
assert old in s
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('row 92 closed')
