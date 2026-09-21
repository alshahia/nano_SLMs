import io
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()
i = s.index('| E-53 |')
eol = s.index('\n', i)
line = ('| E-54 | 2026-09-19 | DA-7 Redact-analogue: Arabic NER token tagger (hashed char n-grams, CPU) ' +
'+ deterministic regex rules (Arabic-digit phones, IDs, dates, URLs/emails) mirroring their hybrid design; ' +
'+ en tokens as second row (MultiNERD en). bar: span/token F1 beats all-O baseline +0.05 |')
s = s[:eol+1] + line + s[eol+1:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('E-54 registered BEFORE results')
