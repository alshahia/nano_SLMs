import json, collections, torch, sys, pathlib
sys.path.insert(0, '.')
DATA = 'data/langid/emo'
rows = []
for line in open(DATA + '/train.tsv', encoding='utf-8'):
    parts = line.rstrip('\n').split('\t')
    rows.append(int(parts[1]))
cnt = collections.Counter(rows)
K = 160
w = torch.tensor([1.0 / max(cnt[k], 1) ** 0.5 for k in range(K)])
print('mean', float(w.mean()), 'median', float(w.median()), 'min', float(w.min()), 'max', float(w.max()), 'cnt210', cnt.most_common(3))
lab = torch.tensor(rows[:10000])
torch.manual_seed(0)
logits = torch.zeros(10000, K)
ce = torch.nn.functional.cross_entropy(logits, lab)
cew = torch.nn.functional.cross_entropy(logits, lab, weight=w / w.mean(), label_smoothing=0.1)
print('ce', float(ce), 'cew', float(cew))