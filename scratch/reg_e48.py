import io
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()
anchor_row = '| E-47 | 2026-09-19 | DA-2b arms a/b/c'
i = s.index(anchor_row)
eol = s.index('\n', i)
line = ('| E-48 | 2026-09-19 | DA-3 Gist-analogue topic tagging recreate (ar SANAD 7 topics + en HuffPo top-10; '
        'bar = per-lang top-1 beats frequency prior +0.05) | hashed n-gram bag (CPU) vs freq-prior |')
s = s[:eol+1] + line + s[eol+1:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('E-48 registered BEFORE results')
