import io
p = 'langid/scripts/train_ner.py'
s = io.open(p, encoding='utf-8').read()
old1 = '    lab2id = {l: i for i, l in enumerate(labels)}'.replace(lab2id, lab2id) if False else '    lab2id = {l: i for i, l in enumerate(labels)}'.replace(' `', ' ')
anchor = '    K = len(labels)'
assert anchor in s
s = s.replace(anchor, anchor + '\n    O_ID = lab2id["O"]', 1)
s = s.replace('ent_mask = vb != 0', 'ent_mask = vb != O_ID')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('O_ID patch ok')