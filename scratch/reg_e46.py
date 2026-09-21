import io
p = 'research/EXPERIMENTS.md'
s = io.open(p, encoding='utf-8').read()

tab_prev = '| E-44 | 2026-09-19 |'
_add = '| E-46 | 2026-09-19 | DA-2b arms a/b/c (bigger Arabic emoji corpus; tiny transformer head; weighted CE + label smoothing) fixed D2 bars | best arm by test top-1 on fixed protocol |\n'
anchor_row = '| E-44 | 2026-09-19 | DA-2 Emo-analogue emoji suggestion recreate (ar+en, self-labeled tweets; bar = frequency-prior beats) |'
i = s.index(anchor_row)
eol = s.index('\n', i)
s = s[:eol+1] + tab_prev + '' + s[eol+1:]
eol = s.index('\n', eol+1)
line = '| E-46 | 2026-09-19 | DA-2b arms a/b/c - add 34,514-row Arabic dialects one-type emoji corpus (435 emojis); tiny transformer head; weighted CE + label smoothing | fixed pre-registered bars: test top-1 >= 0.398 (2x prior) AND >= 0.249 (prior+0.05); int8 <=3 MiB; agreement >=0.98 |\n'
s = s[:eol+1] + line + s[eol+1:]
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('E-46 registered')
