import io
p = 'TASKS.md'
s = io.open(p, encoding='utf-8').read()
i = s.index('| 94 | E-53 Muon-on-DA-3')
eol = s.index('\n', i)
line = ('| 95 | DA-7 Redact-analogue Arabic NER (MAFAT, E-54) - **done honest** | `done` | closed 2026-09-19: '
        'entity-token acc 0.398 / macro-F1 0.330 (bar vs all-O PASS); token acc 0.808 < all-O 0.819 (honest FAIL on the acc gate); '
        'pending: deterministic regex layer + span decoding; 3 CPU epochs unweighted ent-acc 0.085 vs weighted 6ep 0.388 - weighting is the lever |')
s = s[:eol+1] + line + s[eol+1:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('row 95 added')