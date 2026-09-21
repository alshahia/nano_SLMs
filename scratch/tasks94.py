import io
p = 'TASKS.md'
s = io.open(p, encoding='utf-8').read()
anchor = '| 93 | DA-3 Gist-analogue topic tagging'
i = s.index(anchor)
eol = s.index('\n', i)
line = ('| 94 | E-53 Muon-on-DA-3 A/B (E-41 lever application, user-approved) - **done** | `done` | closed 2026-09-19: '
        'Muon 3e-2 beats Adam control on both langs in test (ar 0.9268 vs 0.9048, en 0.7300 vs 0.6780); Muon is the new DA-bag default |')
s = s[:eol+1] + line + s[eol+1:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('row 94 added')
