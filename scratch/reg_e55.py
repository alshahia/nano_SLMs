import io
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()
if '| E-55 |' not in s:
    i = s.index('| E-54 |')
    eol = s.index('\n', i)
    line = ('| E-55 | 2026-09-19 | DA-7b deterministic regex redaction layer (their hybrid-design second half): '
    + 'Arabic/Latin-digit runs, dates, phones, URLs/emails, IDs as token rules; measured against gold TIMEX/ANG/DUC test tokens; '
    + 'hybrid = regex override on matched tags. bar: numeric/temporal class token-P >= 0.5 and beats pure-model on that class subset |')
    s = s[:eol+1] + line + s[eol+1:]
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('E-55 registered')
else:
    print('E-55 row already present - skipping')
