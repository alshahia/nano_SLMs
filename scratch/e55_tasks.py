import io
p = 'TASKS.md'
s = io.open(p, encoding='utf-8').read()
i = s.index('| 95 | DA-7 Redact-analogue')
eol = s.index('\n', i)
line = ('| 96 | DA-7b deterministic regex redaction layer (E-55) - **done honest** | `done` | closed 2026-09-19: '
        'test numeric regex P 0.008 / temporal P 0.371 - both under the 0.5 bar: FAIL; model still beats regex on both subsets; '
        'rules kept fallback-only (URL/email/phone/ID); MAFAT news gold not the right substrate for digit/date rules |')
s = s[:eol+1] + line + s[eol+1:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('row 96 added')