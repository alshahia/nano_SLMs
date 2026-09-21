import io
p = 'langid/scripts/train_schemer.py'
s = io.open(p, encoding='utf-8').read()
s = s.replace('    return [[(w, l) for w, l in sent] for sent in out]\n',
              '    return [([w for w, l in sent], [l for w, l in sent]) for sent in out]\n', 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('return: (toks_list, tags_list) per sentence')
