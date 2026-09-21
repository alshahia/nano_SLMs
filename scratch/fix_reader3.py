import io
p = 'langid/scripts/train_schemer.py'
s = io.open(p, encoding='utf-8').read()
s = s.replace('    return [(list(t), list(l)) for t, l in out]\n',
              '    return [[(w, l) for w, l in sent] for sent in out]\n', 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('return fixed to (tok, tag) tuples-per-sentence')
