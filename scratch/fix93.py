import io
p = 'langid/scripts/build_topic_eval.py'
s = io.open(p, encoding='utf-8').read()
lines = s.splitlines()
out = []
skip = False
for L in lines:
    if 
        skip = False
        continue
    if L.strip().startswith('f.write("%s') and L.rstrip().endswith('"'):
        out.append('                f.write("%s\\t%s\\t%s\\n" % (lang, lab2id[lab], s.replace("\\t", " ")))')
        skip = True
        continue
    out.append(L)
io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
print('write line repaired')
