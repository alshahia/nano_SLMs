import pyarrow.parquet as pq
from collections import Counter
t = pq.read_table('data/langid/tmp_tead.parquet')
rows = t.select(['text']).to_pylist()
c = Counter()
n_em = 0
for r in rows:
    s = r['text']
    e = [ch for ch in s if ord(ch) >= 0x1F000 or 0x2600 <= ord(ch) <= 0x27BF]
    if e:
        n_em += 1
        c.update(e)
print('rows with emoji:', n_em, 'unique emoji types:', len(c))
print('top 20:', [(e, n) for e, n in c.most_common(20)])