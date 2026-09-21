import io, re
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()
lines = s.splitlines()
for i, L in enumerate(lines):
    if L.startswith('| E-48 | 2026-09-19 | DA-3'):
        lines[i] = L.replace('| E-48 |', '| E-52 |', 1) + ' CLOSED: DA-3 recreate PASS - ar/en. ' \
            + 'TEST top-1: ar 0.9048 (prior 0.1429; 2x bar 0.2857 PASS, +0.05 bar PASS), en 0.6780 (prior 0.1000; 2x bar 0.2000 PASS, +0.05 PASS). ' \
            + 'top-3 ar 0.9850 / en 0.8830. FP16 EmbeddingBag 2^16x17 = 2.13 MiB. Ethics: en taxonomy = HuffPo editorial buckets (weaker than SANAD news sections).'
        print('renamed + closed at line', i + 1)
        break
else:
    raise SystemExit('row not found')
io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')