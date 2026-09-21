import io
p = 'langid/scripts/export_emo_tf.py'
s = io.open(p, encoding='utf-8').read()
old = '    ids = np.concatenate([ids, [0] * (L - len(ids))])'
new = '    ids = np.concatenate([ids, np.zeros((L - len(ids)), dtype=np.int64)])'
assert old in s
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('concat dtype fixed')
