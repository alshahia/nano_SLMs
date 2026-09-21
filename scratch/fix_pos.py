import io
p = 'langid/scripts/train_rank.py'
s = io.open(p, encoding='utf-8').read()
old = ('            pos = torch.zeros(B, dtype=torch.long, device=ranks.device)\n'
       '            pos[ranks == gold] = torch.arange(B, device=ranks.device)[None, :].expand(B, B)[ranks == gold]')
new = ('            pos = torch.zeros(B, dtype=torch.long, device=ranks.device)\n'
       '            pos = (ranks == gold).float().argmax(dim=1)')
assert old in s
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('pos fix')
