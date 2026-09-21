import io
p = 'langid/scripts/build_topic_eval.py'
lines = io.open(p, encoding='utf-8').read().splitlines()
out = []
skip = False
for L in lines:
    if skip:
        skip = False
        continue
    if 'f.write' in L and 'lab2id' in L:
        out.append("                f.write(\"%s\\t%s\\t%s\\n\" % (lang, lab2id[lab], s.replace(\"\\t\", \" \")))")
        skip = True
        continue
    out.append(L)
io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
print('repaired line 93-94')