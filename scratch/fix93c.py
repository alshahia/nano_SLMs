import io
p = 'langid/scripts/build_topic_eval.py'
lines = io.open(p, encoding='utf-8').read().splitlines()
out = []
i = 0
while i < len(lines):
    L = lines[i]
    if 'f.write' in L:
        out.append("                f.write(\"%s\\t%s\\t%s\\n\" % (lang, lab2id[lab], s.replace(\"\\t\", \" \")))")
        i += 2
        continue
    out.append(L)
    i += 1
io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
print('ok')