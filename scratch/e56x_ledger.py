import io
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()
i = s.index('CLOSED PASS (bar = batch-64 R@1')
i = s.index('Next lever on en: more epochs (en curve still climbing at ep4).', i)
s = s[:i] + ('UPDATE 2026-09-20: en extended to 12 epochs w/ patience-4 early-stop added to trainer; en curve rose all 12 epochs (0.057->0.313 val R@1, no overfit signature; train loss fell in step), TEST now R@1 0.3211 (21x chance) / R@10 0.6786. Persistence add-on: best-on-val checkpoint keeps selection clean.') + s[i+len('Next lever on en: more epochs (en curve still climbing at ep4).'):]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ledger updated')