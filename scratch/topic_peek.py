import json, collections
import pyarrow.parquet as pq
t = pq.read_table('data/langid/raw/huff_top10.json'.replace('.json', '_NONE_none')) if False else None
j = json.load(open('data/langid/raw/huff_top10.json', encoding='utf-8'))
print(type(j), len(j))
row = j[0] if isinstance(j, list) else next(iter(j.items()))
row2 = j[1]
print({k: (str(v)[:60].encode('ascii', 'replace').decode()) for k, v in row2.items()})
from collections import Counter
cats = Counter(r.get('category') for r in j)
print(cats)
t2 = pq.read_table('data/langid/raw/sanad.parquet')
print(t2.schema)
sc = t2.column('label').to_pylist()
print(Counter(sc))