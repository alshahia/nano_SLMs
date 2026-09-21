import io
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()
i = s.index('| E-53 |')
eol = s.index('\n', i)
lines = s.splitlines()
lines[i] = lines[i].rstrip() + (' CLOSED: Muon (E-41 NS5 recipe, 1-D params plain SGDM) transfers to the DA-3 hashed bag. '
  'TEST top-1: Adam 0.25lr ar 0.9048/en 0.6780 (E-52); Muon 1e-2 ar 0.9338/en 0.6965; Muon 3e-2 ar 0.9268/en 0.7300 (best en). '
  'Pre-registered gate: Muon best per-lang beats Adam control (ar +2.2pp 3e-2 / +2.9pp 1e-2; en +5.2pp 3e-2) -> PASS. '
  'E-41 lever thereby extends from trunk pretraining to sparse-lookup classifier heads; new default optimizer for DA-line bag heads = Muon 3e-2.')
io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
print('E-53 closed')
