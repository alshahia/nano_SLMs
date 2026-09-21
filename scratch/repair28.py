import io, re
p = 'langid/scripts/build_topic_eval.py'
s = io.open(p, encoding='utf-8').read()
lines = s.splitlines()
out = []
skip_next = False
for i, L in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
    if L.startswith('    t = t.replace('):
        out.append('    t = t.replace(chr(13), " ").replace(chr(10), " ").replace(chr(9), " ")')
        # the fragments on the following lines up to return are junk
        while out and False:
            pass
        skip_done = True
    else:
        out.append(L)
s2 = '\n'.join(out) + '\n'
io.open(p, 'w', encoding='utf-8', newline='\n').write(s2)
print('repaired')