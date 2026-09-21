import io
p = 'langid/scripts/export_emo_tf.py'
s = io.open(p, encoding='utf-8').read()
old = '    pad = ids == 0'
new = '    ids = ids.astype(np.int64)\n    pad = ids == 0'
assert old in s
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('pad-line ids to int64')