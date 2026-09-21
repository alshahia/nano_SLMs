import io
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()
anchor = s.rindex('\n')
line = ('| E-53 | 2026-09-19 | E-41 Muon lever applied to DA-3 bag topic model: Adam lr 0.25 (E-52 control) vs Muon 1e-2 / 3e-2 on emb+bias, identical data/batches/seed | 2-3 arms CPU |')
# insert after the E-52 ledger row line
i = s.index('| E-52 |')
eol = s.index('\n', i)
s = s[:eol+1] + line + s[eol+1:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('E-53 registered BEFORE results')
