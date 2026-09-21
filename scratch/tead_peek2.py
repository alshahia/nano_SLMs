import pyarrow.parquet as pq
t = pq.read_table('data/langid/tmp_tead.parquet')
rows = t.select(['text']).to_pylist()
adv = sum(any(ord(c) >= 0x1F000 for c in r['text']) for r in rows)
print('rows', len(rows), 'astral-emoji:', adv)