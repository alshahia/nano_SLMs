import io
p = 'langid/scripts/train_emo.py'
s = io.open(p, encoding='utf-8').read()
old = "        w = torch.tensor([1.0 / max(cnt[k], 1) ** 0.5 for k in range(K)], dtype=torch.float32)\n        weights = (w / w.median()).clamp(max=3.0)"
new = "        w = torch.tensor([1.0 / max(cnt[k], 1) ** 0.5 for k in range(K)], dtype=torch.float32)\n        weights = w / w.mean()"  # mean-normalized: total loss scale preserved
assert old in s
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('weights fixed')