import io
p = 'langid/src/emo_model.py'
s = io.open(p, encoding='utf-8').read()
s = s.replace('f = list(features.text_features(t))', 'f = list(emo_features(t))')
if 'def emo_features' not in s:
    raise SystemExit('emo_features missing')
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched')
