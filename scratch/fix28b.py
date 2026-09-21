import io
p = 'langid/scripts/build_topic_eval.py'
s = io.open(p, encoding='utf-8').read()
lines = s.splitlines()
out = [L for i, L in enumerate(lines) if i not in (28, 29)]  # 0-based lines 29,30
io.open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
print('dropped junk lines')