import os, pyarrow.parquet as pq
p = os.path.abspath('data/langid/raw/tead.parquet')
print('exists:', os.path.exists(p))
t = pq.read_table(p)
print(t.schema)
print(t.num_rows)