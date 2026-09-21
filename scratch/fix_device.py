import io
p = 'langid/scripts/train_rank.py'
s = io.open(p, encoding='utf-8').read()
old = '                                                     torch.arange(len(idx)))'
assert old in s
s = s.replace(old, '                                                     torch.arange(len(idx), device=ha.device))', 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('device fix')
