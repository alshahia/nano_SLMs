import json, collections
cats = collections.Counter()
n = 0
first = None
for line in open('data/langid/raw/huff_top10.json', encoding='utf-8'):
    r = json.loads(line)
    n += 1
    if first is None: first = r
    cats[r.get('category')] += 1
print(n)
print({k: (str(k)[:40].encode('ascii', 'replace').decode() if not isinstance(k, str) else k) for k in list(cats)[:12]})
print('first keys:', list(first.keys()))
print('first:', {k: str(v)[:50].encode('ascii', 'replace').decode() for k, v in first.items()})
import pyarrow.parquet as pq
t2 = pq.read_table('data/langid/raw/sanad.parquet')
print(t2.schema)
print(collections.Counter(t2.column('label').to_pylist()))