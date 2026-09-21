import io
p = 'langid/scripts/export_emo_tf.py'
s = io.open(p, encoding='utf-8').read()
s = s.replace('    ids = ids.numpy()[: emo_model.MAX_LEN]', '    ids = ids.numpy().astype(np.int64)[: emo_model.MAX_LEN]')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('dtype fix')