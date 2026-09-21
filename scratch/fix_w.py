import io
p = 'langid/scripts/train_schemer.py'
s = io.open(p, encoding='utf-8').read()
old = 'w = torch.tensor([cnt[k] ** -0.5 for k in range(K)])'
assert old in s
s = s.replace(old, old.replace('cnt[k]', 'max(cnt[k], 1)') + "  # zero-count classes exist in schemer vocab", 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('weighted fix')
