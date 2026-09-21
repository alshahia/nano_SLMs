import io
p = 'langid/scripts/export_emo_tf.py'
s = io.open(p, encoding='utf-8').read()
old = '    ids = ids.numpy().astype(np.int64)[: emo_model.MAX_LEN]'
if old not in s:
    old2 = '    ids = ids.numpy()[: emo_model.MAX_LEN]'
    assert old2 in s, 'no anchor'
    s = s.replace(old2, old, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ensure dtype fix')