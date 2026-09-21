import io
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()
s = s.replace('| E-46 | 2026-09-19 | DA-2b arms a/b/c', '| E-47 | 2026-09-19 | DA-2b arms a/b/c', 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('renamed to E-47')