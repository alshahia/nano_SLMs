import io
p = 'langid/scripts/build_schemer.py'
s = io.open(p, encoding='utf-8').read()
s = s.replace('    rng.shuffle(0)\n', '')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('removed bogus shuffle')
