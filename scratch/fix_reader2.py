import io
p = 'langid/scripts/train_schemer.py'
s = io.open(p, encoding='utf-8').read()
bad = '    out = []'
s = s.replace(bad, 'def read_sents(p):\n    out = []', 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('def restored')
