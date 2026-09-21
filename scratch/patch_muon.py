import io
p = 'langid/scripts/train_topic.py'
s = io.open(p, encoding='utf-8').read()
old = '                u = (p.grad + mom * buf) if mom != 0 else buf'
assert s.count(old) == 1, 'anchor count %d' % s.count(old)
new = old + chr(10) + '                if p.ndim < 2:  # bias: plain SGDM (NS5 needs a matrix)' + chr(10) + '                    p.add_(buf, alpha=-lr)' + chr(10) + '                else:'
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('muon step patched')