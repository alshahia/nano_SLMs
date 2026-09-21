import io
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()
# find end of E-56 row block: append E-57 row after last E-56 table line
i = s.index('| E-56 |')
e = s.index('\n', s.index('Next: more epochs on en (curve still climbing at ep4).', i)) if 'Next: more epochs' in s else s.index('\n', i)
# fallback: insert after full line of i
e = s.index('\n', i + 5)
row = '| E-57 | DA-9 Schemer (Arabic schema slots) | token-level hashed tagger (E-54 recipe reuse) over synthetic-template corpus (DATE_G/H/REL, TIME, NUM_AI; fillers from real asas text); deterministic-harness rules as baseline comparison; bar pre-registered: strict span-F1 >= 0.75 on held-out synthetic test AND micro-F1 >= rules-only baseline | PENDING |'
s = s[:e+1] + row + s[e+1:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('E-57 registered (row-first)')
